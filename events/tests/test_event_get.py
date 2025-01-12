# -*- coding: utf-8 -*-
from .utils import versioned_reverse as reverse
import pytest
from .utils import get, assert_fields_exist
from events.models import (
    Event, PublicationStatus, Language
)


# === util methods ===

def get_list(api_client, version='v1', data=None, query_string=None):
    url = reverse('event-list', version=version)
    if query_string:
        url = '%s?%s' % (url, query_string)
    return get(api_client, url, data=data)


def get_detail(api_client, detail_pk, version='v1', data=None):
    detail_url = reverse('event-detail', version=version, kwargs={'pk': detail_pk})
    return get(api_client, detail_url, data=data)


def assert_event_fields_exist(data, version='v1'):
    # TODO: incorporate version parameter into version aware
    # parts of test code
    fields = (
        '@context',
        '@id',
        '@type',
        'audience',
        'created_time',
        'custom_data',
        'data_source',
        'date_published',
        'description',
        'end_time',
        'event_status',
        'external_links',
        'id',
        'images',
        'in_language',
        'info_url',
        'keywords',
        'last_modified_time',
        'location',
        'location_extra_info',
        'name',
        'offers',
        'provider',
        'provider_contact_info',
        'publisher',
        'short_description',
        'audience_min_age',
        'audience_max_age',
        'start_time',
        'sub_events',
        'super_event',
        'super_event_type',
    )
    if version == 'v0.1':
        fields += (
            'origin_id',
            'headline',
            'secondary_headline',
        )
    assert_fields_exist(data, fields)


# === tests ===

@pytest.mark.django_db
def test_get_event_list_html_renders(api_client, event):
    url = reverse('event-list', version='v1')
    response = api_client.get(url, data=None, HTTP_ACCEPT='text/html')
    assert response.status_code == 200, str(response.content)


@pytest.mark.django_db
def test_get_event_list_check_fields_exist(api_client, event):
    """
    Tests that event list endpoint returns the correct fields.
    """
    response = get_list(api_client)
    assert_event_fields_exist(response.data['data'][0])


@pytest.mark.django_db
def test_get_event_detail_check_fields_exist(api_client, event):
    """
    Tests that event detail endpoint returns the correct fields.
    """
    response = get_detail(api_client, event.pk)
    assert_event_fields_exist(response.data)


@pytest.mark.django_db
def test_get_unknown_event_detail_check_404(api_client):
    response = api_client.get(reverse('event-detail', kwargs={'pk': 'möö'}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_event_list_verify_text_filter(api_client, event, event2):
    response = get_list(api_client, data={'text': 'event'})
    assert event.id not in [entry['id'] for entry in response.data['data']]
    assert event2.id in [entry['id'] for entry in response.data['data']]


@pytest.mark.django_db
def test_get_event_list_verify_data_source_filter(api_client, data_source, event, event2):
    response = get_list(api_client, data={'data_source': data_source.id})
    assert event.id in [entry['id'] for entry in response.data['data']]
    assert event2.id not in [entry['id'] for entry in response.data['data']]


@pytest.mark.django_db
def test_get_event_list_verify_data_source_negative_filter(api_client, data_source, event, event2):
    response = get_list(api_client, data={'data_source!': data_source.id})
    assert event.id not in [entry['id'] for entry in response.data['data']]
    assert event2.id in [entry['id'] for entry in response.data['data']]


@pytest.mark.django_db
def test_get_event_list_verify_location_filter(api_client, place, event, event2):
    response = get_list(api_client, data={'location': place.id})
    assert event.id in [entry['id'] for entry in response.data['data']]
    assert event2.id not in [entry['id'] for entry in response.data['data']]


@pytest.mark.django_db
def test_get_event_list_verify_keyword_filter(api_client, keyword, event):
    event.keywords.add(keyword)
    response = get_list(api_client, data={'keyword': keyword.id})
    assert event.id in [entry['id'] for entry in response.data['data']]
    response = get_list(api_client, data={'keyword': 'unknown_keyword'})
    assert event.id not in [entry['id'] for entry in response.data['data']]


@pytest.mark.django_db
def test_get_event_list_verify_division_filter(api_client, event, event2, event3, administrative_division,
                                               administrative_division2):
    event.location.divisions = [administrative_division]
    event2.location.divisions = [administrative_division2]

    # filter using one value
    response = get_list(api_client, data={'division': administrative_division.ocd_id})
    data = response.data['data']
    assert len(data) == 1
    assert event.id in [entry['id'] for entry in data]

    # filter using two values
    filter_value = '%s,%s' % (administrative_division.ocd_id, administrative_division2.ocd_id)
    response = get_list(api_client, data={'division': filter_value})
    data = response.data['data']
    assert len(data) == 2
    ids = [entry['id'] for entry in data]
    assert event.id in ids
    assert event2.id in ids


@pytest.mark.django_db
def test_get_event_list_super_event_filters(api_client, event, event2):
    event.super_event_type = Event.SuperEventType.RECURRING
    event.save()
    event2.super_event = event
    event2.save()

    # fetch non-subevents
    response = get_list(api_client, query_string='super_event=none')
    assert len(response.data['data']) == 1
    assert response.data['data'][0]['id'] == event.id

    # fetch subevents
    response = get_list(api_client, query_string='super_event='+event.id)
    assert len(response.data['data']) == 1
    assert response.data['data'][0]['id'] == event2.id


@pytest.mark.django_db
def test_get_event_list_recurring_filters(api_client, event, event2):
    event.super_event_type = Event.SuperEventType.RECURRING
    event.save()
    event2.super_event = event
    event2.save()

    # fetch superevents
    response = get_list(api_client, query_string='recurring=super')
    assert len(response.data['data']) == 1
    assert response.data['data'][0]['id'] == event.id

    # fetch subevents
    response = get_list(api_client, query_string='recurring=sub')
    assert len(response.data['data']) == 1
    assert response.data['data'][0]['id'] == event2.id


@pytest.mark.django_db
def test_super_event_type_filter(api_client, event, event2):
    event.super_event_type = Event.SuperEventType.RECURRING
    event.save()
    event2.super_event = event
    event2.save()

    # "none" and "null" should return only the non super event
    for value in ('none', 'null'):
        response = get_list(api_client, query_string='super_event_type=%s' % value)
        ids = {e['id'] for e in response.data['data']}
        assert ids == {event2.id}

    # "recurring" should return only the recurring super event
    response = get_list(api_client, query_string='super_event_type=recurring')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event.id}

    # "recurring,none" should return both
    response = get_list(api_client, query_string='super_event_type=recurring,none')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event.id, event2.id}

    response = get_list(api_client, query_string='super_event_type=fwfiuwhfiuwhiw')
    assert len(response.data['data']) == 0


@pytest.mark.django_db
def test_get_event_disallow_simultaneous_include_super_and_sub(api_client, event, event2):
    event.super_event_type = Event.SuperEventType.RECURRING
    event.save()
    event2.super_event = event
    event2.save()

    # fetch event with super event
    detail_url = reverse('event-detail', version='v1', kwargs={'pk': event2.pk})

    # If not specifically handled, the following combination of
    # include parameters causes an infinite recursion, because the
    # super events of sub events of super events ... are expanded ad
    # infinitum. This test is here to check that execution finishes.
    detail_url += '?include=super_event,sub_events'
    response = get(api_client, detail_url)
    assert_event_fields_exist(response.data)
    assert(type(response.data['super_event'] == 'dict'))


@pytest.mark.django_db
def test_language_filter(api_client, event, event2, event3):
    event.name_sv = 'namn'
    event.save()
    event2.in_language.add(Language.objects.get_or_create(id='en')[0])
    event2.in_language.add(Language.objects.get_or_create(id='sv')[0])
    event2.save()
    event3.name_ru = 'название'
    event3.in_language.add(Language.objects.get_or_create(id='et')[0])
    event3.save()

    # Finnish should be the default language
    response = get_list(api_client, query_string='language=fi')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event.id, event2.id, event3.id}

    # Swedish should have two events (matches in_language and name_sv)
    response = get_list(api_client, query_string='language=sv')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event.id, event2.id}

    # English should have one event (matches in_language)
    response = get_list(api_client, query_string='language=en')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event2.id}

    # Russian should have one event (matches name_ru)
    response = get_list(api_client, query_string='language=ru')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event3.id}

    # Chinese should have no events
    response = get_list(api_client, query_string='language=zh_hans')
    ids = {e['id'] for e in response.data['data']}
    assert ids == set()

    # Estonian should have one event (matches in_language), even without translations available
    response = get_list(api_client, query_string='language=et')
    ids = {e['id'] for e in response.data['data']}
    assert ids == {event3.id}


@pytest.mark.django_db
def test_event_list_filters(api_client, event, event2):
    filters = (
        ([event.publisher.id, event2.publisher.id], 'publisher'),
        ([event.data_source.id, event2.data_source.id], 'data_source'),
    )

    for filter_values, filter_name in filters:
        q = ','.join(filter_values)
        response = get_list(api_client, query_string='%s=%s' % (filter_name, q))
        data = response.data['data']
        assert(len(data) == 2)
        ids = [e['id'] for e in data]
        assert event.id in ids
        assert event2.id in ids


@pytest.mark.django_db
def test_publication_status_filter(api_client, event, event2, user, organization, data_source):
    event.publication_status = PublicationStatus.PUBLIC
    event.save()

    event2.publication_status = PublicationStatus.DRAFT
    event2.save()

    api_client.force_authenticate(user=user)

    response = get_list(api_client, query_string='show_all=true&publication_status=public')
    ids = {e['id'] for e in response.data['data']}
    assert event.id in ids
    assert event2.id not in ids

    # cannot see drafts from other organizations
    response = get_list(api_client, query_string='show_all=true&publication_status=draft')
    ids = {e['id'] for e in response.data['data']}
    assert event2.id not in ids
    assert event.id not in ids

    event2.publisher = organization
    event2.data_source = data_source
    event2.save()

    response = get_list(api_client, query_string='show_all=true&publication_status=draft')
    ids = {e['id'] for e in response.data['data']}
    assert event2.id in ids
    assert event.id not in ids


@pytest.mark.django_db
def test_admin_user_filter(api_client, event, event2, user):
    api_client.force_authenticate(user=user)

    response = get_list(api_client, query_string='admin_user=true')
    ids = {e['id'] for e in response.data['data']}
    assert event.id in ids
    assert event2.id not in ids
