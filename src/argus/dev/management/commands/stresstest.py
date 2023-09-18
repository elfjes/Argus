from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
import itertools

import httpx
from httpx import AsyncClient, TimeoutException, HTTPStatusError

from django.core.management.base import BaseCommand


class DatabaseMismatchError(Exception):
    pass


class Command(BaseCommand):
    help = "Stresstests incident creation API"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            type=str,
            help="URL for target argus host including port, ex https://argushost.no:443",
        )
        parser.add_argument(
            "token",
            type=str,
            help="Token for authenticating against target API. The token must belong to a user that is associated with a source system",
        )
        parser.add_argument(
            "-s",
            "--seconds",
            type=int,
            help="Number of seconds to send http requests. After this no more requests will be sent but responses will be waited for. Default 10s",
            default=10,
        )
        parser.add_argument("-t", "--timeout", type=int, help="Timeout for requests. Default 5s", default=5)
        parser.add_argument("-w", "--workers", type=int, help="Number of workers. Default 1s", default=1)
        parser.add_argument("-b", "--bulk", action="store_true", help="Bulk ACK created incidents")

    def handle(self, *args, **options):
        tester = StressTester(options.get("url"), options.get("token"), options.get("timeout"), options.get("workers"))
        loop = asyncio.get_event_loop()
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=options.get("seconds"))
        self.stdout.write("Running stresstest ...")
        try:
            incident_ids = loop.run_until_complete(tester.run_stresstest_workers(end_time))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Completed in {datetime.now() - start_time} after sending {len(incident_ids)} requests."
                )
            )
            self.stdout.write("Verifying incidents were created correctly ...")
            loop.run_until_complete(tester.run_verification_workers(incident_ids))
            self.stdout.write(self.style.SUCCESS("Verification complete with no errors."))
            if options.get("bulk"):
                self.stdout.write("Bulk ACKing incidents ...")
                tester.bulk_ack(incident_ids)
                self.stdout.write(self.style.SUCCESS("Succesfully bulk ACK'd"))
        except (DatabaseMismatchError, HTTPStatusError, TimeoutException) as e:
            self.stderr.write(self.style.ERROR(e))
            return


class StressTester:
    def __init__(self, url, token, timeout, worker_count):
        self.url = url
        self.token = token
        self.timeout = timeout
        self.worker_count = worker_count

    def _get_incident_data(self):
        return {
            "start_time": datetime.now().isoformat(),
            "description": "Stresstest",
            "tags": [{"tag": "problem_type=stresstest"}],
        }

    def _get_auth_header(self):
        return {"Authorization": f"Token {self.token}"}

    def _get_incidents_v1_url(self):
        return urljoin(self.url, "/api/v1/incidents/")

    def _get_incidents_v2_url(self):
        return urljoin(self.url, "/api/v2/incidents/")

    async def _post_incidents_until_end_time(self, end_time, client):
        created_ids = []
        incident_data = self._get_incident_data()
        while datetime.now() < end_time:
            try:
                response = await client.post(
                    self._get_incidents_v1_url(), json=incident_data, headers=self._get_auth_header()
                )
                response.raise_for_status()
                incident = response.json()
                created_ids.append(incident["pk"])
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for POST response to {self.url}")
            except HTTPStatusError as e:
                msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
        return created_ids

    async def run_stresstest_workers(self, end_time):
        async with AsyncClient(timeout=self.timeout) as client:
            results = await asyncio.gather(
                *(self._post_incidents_until_end_time(end_time, client) for _ in range(self.worker_count))
            )
            return list(itertools.chain.from_iterable(results))

    async def run_verification_workers(self, incident_ids):
        ids = incident_ids.copy()
        async with AsyncClient(timeout=self.timeout) as client:
            await asyncio.gather(*(self._verify_created_incidents(ids, client) for _ in range(self.worker_count)))

    async def _verify_created_incidents(self, incident_ids, client):
        expected_data = self._get_incident_data()
        while incident_ids:
            incident_id = incident_ids.pop()
            id_url = urljoin(self._get_incidents_v1_url(), str(incident_id) + "/")
            try:
                response = await client.get(id_url, headers=self._get_auth_header())
                response.raise_for_status()
            except TimeoutException:
                raise TimeoutException(f"Timeout waiting for GET response to {id_url}")
            except HTTPStatusError as e:
                msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
                raise HTTPStatusError(msg, request=e.request, response=e.response)
            response_data = response.json()
            self._verify_tags(response_data, expected_data)
            self._verify_description(response_data, expected_data)

    def _verify_tags(self, response_data, expected_data):
        expected_tags = set([tag["tag"] for tag in expected_data["tags"]])
        response_tags = set([tag["tag"] for tag in response_data["tags"]])
        if expected_tags != response_tags:
            msg = f'Actual tag(s) "{response_tags}" differ from expected tag(s) "{expected_tags}"'
            raise DatabaseMismatchError(msg)

    def _verify_description(self, response_data, expected_data):
        expected_descr = expected_data["description"]
        response_descr = response_data["description"]
        if response_descr != expected_descr:
            msg = f'Actual description "{response_descr}" differ from expected description "{expected_descr}"'
            raise DatabaseMismatchError(msg)

    def bulk_ack(self, incident_ids):
        request_data = {
            "ids": incident_ids,
            "ack": {
                "timestamp": datetime.now().isoformat(),
                "description": "Stresstest",
            },
        }
        url = urljoin(self._get_incidents_v2_url(), "acks/bulk/")
        try:
            response = httpx.post(url, json=request_data, headers=self._get_auth_header())
            response.raise_for_status()
        except TimeoutException:
            raise TimeoutException(f"Timeout waiting for POST response to {url}")
        except HTTPStatusError as e:
            msg = f"HTTP error {e.response.status_code}: {e.response.content.decode('utf-8')}"
            raise HTTPStatusError(msg, request=e.request, response=e.response)
