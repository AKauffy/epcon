# coding: utf-8

from __future__ import unicode_literals, absolute_import, print_function

from django.conf import settings

from model_utils import Choices

from assopy.models import Vat, VatFare
from conference.models import Fare, FARE_TICKET_TYPES


# due to historical reasons this one is basically hardcoded in various places.
SOCIAL_EVENT_FARE_CODE = 'VOUPE03'
SPECIAL_CODES = [SOCIAL_EVENT_FARE_CODE]

FARE_CODE_TYPES = Choices(
    ("E", "EARLY_BIRD", "Early Bird"),
    ("R", "REGULAR",    "Regular"),
    ("D", "ON_DESK",    "On Desk"),
)

FARE_CODE_VARIANTS = Choices(
    ("S", "STANDARD", "Standard"),
    ("L", "LIGHT",    "Standard Light (no trainings)"),
    ("D", "DAYPASS",  "Day Pass"),
)

FARE_CODE_GROUPS = Choices(
    ("S", "STUDENT",  "Student"),
    ("P", "PERSONAL", "Personal"),
    ("C", "COMPANY",  "Company"),
)

FARE_CODE_REGEXES = {
    "types": {
        FARE_CODE_TYPES.EARLY_BIRD:  "^TE..$",
        FARE_CODE_TYPES.REGULAR:     "^TR..$",
        FARE_CODE_TYPES.ON_DESK:     "^TD..$",
    },
    "variants": {
        FARE_CODE_VARIANTS.STANDARD: "^T.S.$",
        FARE_CODE_VARIANTS.LIGHT:    "^T.L.$",
        FARE_CODE_VARIANTS.DAYPASS:  "^T.D.$",
    },
    "groups": {
        FARE_CODE_GROUPS.STUDENT:    "^T..S$",
        FARE_CODE_GROUPS.PERSONAL:   "^T..P$",
        FARE_CODE_GROUPS.COMPANY:    "^T..C$",
    }
}


def available_fare_codes():
    fare_codes = {
        "T" + type_code + variant_code + group_code:
        "%s %s %s" % (type_name, variant_name, group_name)

        for type_code, type_name       in FARE_CODE_TYPES._doubles
        for variant_code, variant_name in FARE_CODE_VARIANTS._doubles
        for group_code, group_name     in FARE_CODE_GROUPS._doubles
    }

    fare_codes[SOCIAL_EVENT_FARE_CODE] = "Social Event"
    return fare_codes


def is_fare_code_valid(fare_code):
    return fare_code in available_fare_codes()


def create_fare(code, name, price, start_validity, end_validity, vat_rate):

    assert is_fare_code_valid(code)
    assert isinstance(vat_rate, Vat)
    assert start_validity <= end_validity

    if code == SOCIAL_EVENT_FARE_CODE:
        ticket_type = FARE_TICKET_TYPES.event
    else:
        ticket_type = FARE_TICKET_TYPES.conference

    recipient_type = code[3].lower()  # same as lowercase last letter of code

    fare, _ = Fare.objects.get_or_create(
        conference=settings.CONFERENCE_CONFERENCE,
        code=code,
        name=name,
        defaults=dict(
            description=name,
            price=price,
            recipient_type=recipient_type,
            ticket_type=ticket_type,
            start_validity=start_validity,
            end_validity=end_validity,
        )
    )
    VatFare.objects.get_or_create(fare=fare, vat=vat_rate)
    return fare


def pre_create_typical_fares_for_conference(conference, vat_rate,
                                            print_output=False):

    fare_codes = available_fare_codes()
    fares = []

    for fare_code, fare_name in fare_codes.items():
        fare = create_fare(
            code=fare_code, name=fare_name,
            price=1000,  # high random price, we'll change it later
            start_validity=None, end_validity=None,
            vat_rate=vat_rate,
        )
        if print_output:
            print("Created fare %s" % fare)
        fares.append(fare)

    return fares


def set_early_bird_fare_dates(conference, start_date, end_date):
    early_birds = Fare.objects.filter(
        conference=conference,
        code__regex=FARE_CODE_REGEXES['types'][FARE_CODE_TYPES.EARLY_BIRD]
    )
    assert early_birds.count() == 9  # 3**2
    early_birds.update(start_validity=start_date, end_validity=end_date)


def set_regular_fare_dates(conference, start_date, end_date):
    fares = Fare.objects.filter(
        conference=conference,
        code__regex=FARE_CODE_REGEXES['types'][FARE_CODE_TYPES.REGULAR]
    )
    assert fares.count() == 9  # 3**2
    fares.update(start_validity=start_date, end_validity=end_date)
