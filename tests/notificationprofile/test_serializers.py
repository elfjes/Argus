from collections import OrderedDict
import datetime

from django.db import IntegrityError
from django.test import TestCase

from rest_framework.test import APIRequestFactory

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import DestinationConfigFactory, TimeslotFactory
from argus.notificationprofile.media import MEDIA_CLASSES_DICT
from argus.notificationprofile.models import Timeslot
from argus.notificationprofile.serializers import RequestDestinationConfigSerializer, TimeslotSerializer


class TimeslotSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        # When creating a User which is a person, we also create a default Timeslot
        self.default_timeslot = Timeslot.objects.get(user=self.user)
        self.request_factory = APIRequestFactory()

    def test_validate_new_timeslot(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "name": "vfrgthj",
            "time_recurrences": [
                {
                    "days": [1, 2, 3, 4, 5],
                    "start": "00:00:00",
                    "end": "16:00:00",
                }
            ],
        }
        serializer = TimeslotSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validate_new_timeslot_with_duplicate_name(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "name": self.default_timeslot.name,
            "time_recurrences": [
                {
                    "days": [1, 2, 3, 4, 5],
                    "start": "00:00:00",
                    "end": "16:00:00",
                }
            ],
        }
        serializer = TimeslotSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_create_new_timeslot(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "name": "vfrgthj",
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        obj = serializer.create(validated_data)
        self.assertEqual(obj.name, "vfrgthj")

    def test_create_new_timeslot_with_duplicate_name(self):
        request = self.request_factory.post("/")
        request.user = self.user
        # Reuse the name of the default timeslot
        validated_data = {
            "name": self.default_timeslot.name,
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        # serializer.create works on already validated data
        with self.assertRaises(IntegrityError):
            obj = serializer.create(validated_data)

    def test_update_existing_timeslot(self):
        timeslot = TimeslotFactory(name="existing name", user=self.user)
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "name": "new name",
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        obj = serializer.update(timeslot, validated_data)
        self.assertEqual(obj.name, "new name")

    def test_update_existing_timeslot_with_duplicate_name(self):
        timeslot = TimeslotFactory(name="existing name", user=self.user)
        request = self.request_factory.post("/")
        request.user = self.user
        # Reuse the name of the default timeslot
        validated_data = {
            "name": self.default_timeslot.name,
            "time_recurrences": [
                OrderedDict([("days", {1, 2, 3, 4, 5}), ("start", datetime.time(8, 0)), ("end", datetime.time(16, 0))])
            ],
            "user": self.user,
        }
        serializer = TimeslotSerializer(
            context={"request": request},
        )
        # serializer.create works on already validated data
        with self.assertRaises(IntegrityError):
            obj = serializer.update(timeslot, validated_data)


class DestinationConfigSerializerTests(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.request_factory = APIRequestFactory()

    def test_validate_new_email_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {
                "email_address": "user@example.com",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validate_new_email_destination_with_empty_settings(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_validate_new_email_destination_with_invalid_settings(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {"phone_number": "+4747474747"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_validate_new_email_destination_with_invalid_email_address(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {"email_address": "hello"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_validate_new_email_destination_with_additional_settings(self):
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "email",
            "settings": {
                "email_address": "user@example.com",
                "extra_key": "something",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["settings"],
            {
                "email_address": "user@example.com",
                "synced": False,
            },
        )

    def test_create_new_email_destination(self):
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "email",
            "settings": {
                "email_address": "user@example.com",
                "synced": False,
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.create(validated_data)
        self.assertEqual(
            obj.settings,
            {
                "email_address": "user@example.com",
                "synced": False,
            },
        )

    def test_update_existing_email_destination(self):
        destination = DestinationConfigFactory(user=self.user, settings={"email_address": "user@example.com"})

        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "email",
            "settings": {
                "email_address": "new.email@example.com",
                "synced": False,
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.update(destination, validated_data)
        self.assertEqual(obj.settings["email_address"], "new.email@example.com")

    def test_validate_new_sms_destination(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_validate_new_sms_destination_with_empty_settings(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_validate_new_sms_destination_with_invalid_settings(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {"email_address": "user@example.com"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_validate_new_sms_destination_with_invalid_phone_number(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {"phone_number": "+474747"},
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(serializer.errors)

    def test_validate_new_sms_destination_with_additional_settings(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        request = self.request_factory.post("/")
        request.user = self.user
        data = {
            "media": "sms",
            "settings": {
                "phone_number": "+4747474747",
                "extra_key": "something",
            },
        }
        serializer = RequestDestinationConfigSerializer(
            data=data,
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["settings"],
            {
                "phone_number": "+4747474747",
            },
        )

    def test_create_new_sms_destination(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.create(validated_data)
        self.assertEqual(
            obj.settings,
            {
                "phone_number": "+4747474747",
            },
        )

    def test_update_existing_sms_destination(self):
        if not "sms" in MEDIA_CLASSES_DICT.keys():
            self.skipTest("No sms plugin available")
        destination = DestinationConfigFactory(user=self.user, settings={"phone_number": "+4747474747"})

        request = self.request_factory.post("/")
        request.user = self.user
        validated_data = {
            "media_id": "sms",
            "settings": {
                "phone_number": "+4747474747",
            },
            "user": self.user,
        }
        serializer = RequestDestinationConfigSerializer(
            context={"request": request},
        )
        obj = serializer.update(destination, validated_data)
        self.assertEqual(obj.settings["phone_number"], "+4747474747")