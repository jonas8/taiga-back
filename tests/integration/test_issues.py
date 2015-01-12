from unittest import mock
import json

from django.core.urlresolvers import reverse

from taiga.projects.issues import services, models
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_issues_from_bulk():
    data = """
Issue #1
Issue #2
"""
    issues = services.get_issues_from_bulk(data)

    assert len(issues) == 2
    assert issues[0].subject == "Issue #1"
    assert issues[1].subject == "Issue #2"


def test_create_issues_in_bulk(db):
    data = """
Issue #1
Issue #2
"""

    with mock.patch("taiga.projects.issues.services.db") as db:
        issues = services.create_issues_in_bulk(data)
        db.save_in_bulk.assert_called_once_with(issues, None, None)


def test_update_issues_order_in_bulk():
    data = [(1, 1), (2, 2)]

    with mock.patch("taiga.projects.issues.services.db") as db:
        services.update_issues_order_in_bulk(data)
        db.update_in_bulk_with_ids.assert_called_once_with([1, 2], [{"order": 1}, {"order": 2}],
                                                           model=models.Issue)


def test_api_create_issues_in_bulk(client):
    project = f.create_project()
    membership = f.MembershipFactory(project=project, user=project.owner, is_owner=True)

    url = reverse("issues-bulk-create")

    data = {"bulk_issues": "Issue #1\nIssue #2\n",
            "project_id": project.id}

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200, response.data


def test_api_filter_by_subject(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="some random subject", owner=user)
    url = reverse("issues-list") + "?q=some subject"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1, number_of_issues


def test_api_filter_by_text_1(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=one"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1

def test_api_filter_by_text_2(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=this is the issue one"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1

def test_api_filter_by_text_3(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=this is the issue"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 2

def test_api_filter_by_text_4(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=one two"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 0

def test_api_filter_by_text_5(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="python 3", owner=user)
    url = reverse("issues-list") + "?q=python 3"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1


def test_api_filter_by_text_6(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="test", owner=user)
    issue.ref = 123
    issue.save()
    url = reverse("issues-list") + "?q=%s" % (issue.ref)

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1


def test_api_get_issue_by_ref_ok(client):
    user = f.UserFactory(is_superuser=True)
    issue = f.create_issue(subject="test", owner=user)
    issue.ref = 123
    issue.save()
    url = "{}?project={}&ref={}".format(reverse("issues-by-ref"),
                                        issue.project_id,
                                        issue.ref)

    client.login(issue.owner)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data["id"] == issue.id


def test_api_get_issue_by_ref_error_1(client):
    user = f.UserFactory(is_superuser=True)
    issue = f.create_issue(subject="test", owner=user)
    issue.ref = 123
    issue.save()
    url = "{}?project={}&ref={}".format(reverse("issues-by-ref"),
                                        issue.project_id,
                                        issue.ref * 2)

    client.login(issue.owner)
    response = client.get(url)

    assert response.status_code == 404


def test_api_get_issue_by_ref_error_1(client):
    user = f.UserFactory(is_superuser=True)
    issue = f.create_issue(subject="test", owner=user)
    issue.ref = 123
    issue.save()
    url = "{}?project={}&ref={}".format(reverse("issues-by-ref"),
                                        issue.project_id,
                                        "undefined")

    client.login(issue.owner)
    response = client.get(url)

    assert response.status_code == 404
