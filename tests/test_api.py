from time import sleep
from tests.conftest import send_test_email
import pytest
import re

from typing import List

from random_username.generate import generate_username
from requests.models import HTTPError
from pymailtm.api import Account, AccountManager, Domain, DomainManager, DomainNotAvailableException, Message


# Decorator used to make a test skip VCR recording entirely
skip_vcr = pytest.mark.vcr(before_record_request=lambda x: None)


class TestADomain:
    """Test: A Domain..."""

    def test_should_have_all_the_required_fields(self):
        """It should have all the required fields"""
        id_ = "000001"
        domain = "testdomain.com"
        isActive = True
        isPrivate = False
        createdAt = "2021-05-22T00:00:00+00:00"
        updatedAt = "2021-05-22T00:00:00+00:00"

        test_domain = Domain(id_, domain, isActive, isPrivate, createdAt, updatedAt)

        assert test_domain.id == id_
        assert test_domain.domain == domain
        assert test_domain.isActive == isActive
        assert test_domain.isPrivate == isPrivate
        assert test_domain.createdAt == createdAt
        assert test_domain.updatedAt == updatedAt


@pytest.mark.vcr
class TestADomainManager:
    """Test: A DomainManager..."""

    domains: List[Domain]

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        request.cls.domains = DomainManager.get_active_domains()

    def test_should_be_able_to_return_active_domains(self):
        """It should be able to return active domains"""
        assert len(self.domains) > 0
        assert isinstance(self.domains[0], Domain)

    def test_should_be_able_to_get_an_existing_domain_data(self):
        """It should be able to get an existing domain data"""
        domain = self.domains[0]
        domain_data = DomainManager.get_domain(domain.id)
        assert domain.domain == domain_data.domain

    def test_should_raise_an_exception_when_no_domain_with_the_specified_id_is_found(self):
        """It should raise an exception when no domain with the specified id is found"""
        with pytest.raises(HTTPError):
            DomainManager.get_domain("0")


@pytest.mark.vcr
class TestAnAccount:
    """Test: An Account..."""

    def test_should_save_all_required_fields(self):
        """It should save all required fields"""
        id_ = "000011"
        address = "account@testdomain.com"
        quota = 40000
        used = 0
        isDisabled = True
        isDeleted = False
        createdAt = "2021-05-22T00:00:00+00:00"
        updatedAt = "2021-05-22T00:00:00+00:00"
        password = "secure"

        test_account = Account(id_, address, quota, used, isDisabled, isDeleted, createdAt, updatedAt, password)

        assert test_account.id == id_
        assert test_account.address == address
        assert test_account.quota == quota
        assert test_account.used == used
        assert test_account.isDisabled == isDisabled
        assert test_account.isDeleted == isDeleted
        assert test_account.createdAt == createdAt
        assert test_account.updatedAt == updatedAt
        assert test_account.password == password

    def test_can_login_after_being_created(self):
        """It can login after being created"""
        account = AccountManager.new()
        account.login()
        assert type(account.jwt) is str
        assert len(account.jwt) > 0

    def test_should_have_a_method_to_verify_the_login(self):
        """It should have a method to verify the login"""
        account = AccountManager.new()
        assert not account.is_logged_in()
        account.login()
        assert account.is_logged_in()

    def test_should_be_possible_to_delete_it(self):
        """It should be possible to delete it"""
        account = AccountManager.new()
        account.login()
        account.delete()
        with pytest.raises(HTTPError) as err:
            AccountManager.login(account.address, account.password)
        # This is a 401 because the login method tries to get a JWT without success
        assert "401 Client Error: Unauthorized" in err.value.args[0]

    def test_should_raise_an_exception_when_trying_to_delete_an_account_without_login(self):
        """It should raise an exception when trying to delete an account without login"""
        account = AccountManager.new()
        with pytest.raises(HTTPError) as err:
            account.delete()
        assert "401 Client Error: Unauthorized" in err.value.args[0]

    @pytest.mark.timeout(15)
    def test_should_be_able_to_download_its_messages_intro(self):
        """It should be able to download its messages intro."""
        account = AccountManager.new()
        account.login()
        assert len(account.messages) == 0

        send_test_email(account.address)

        messages = []
        while len(messages) == 0:
            sleep(1)
            messages = account.get_all_messages_intro()

        assert len(messages) == 1
        assert isinstance(messages[0], Message)
        assert messages[0].subject == 'subject'
        assert len(account.messages) == 1

    def test_will_raise_an_exception_when_trying_to_download_messages_without_having_logged_in(self):
        """It will raise an exception when trying to download messages without having logged in"""
        account = AccountManager.new()
        with pytest.raises(HTTPError) as err:
            account.get_all_messages_intro()
        assert "401 Client Error: Unauthorized" in err.value.args[0]


@pytest.mark.vcr
class TestAnAccountManager:
    """Test: An AccountManager..."""

    def test_should_be_able_to_generate_a_valid_address_with_no_arguments(self):
        """It should be able to generate a valid address with no arguments"""
        address = AccountManager.generate_address()
        reg = r"[^@]+@[^@]+\.[^@]+"
        assert re.fullmatch(reg, address) is not None

    def test_should_be_able_to_generate_a_valid_address_with_the_provided_arguments(self):
        """It should be able to generate a valid address with the provided arguments"""
        valid_domain = DomainManager.get_active_domains()[0]
        address = AccountManager.generate_address(user="nick", domain=valid_domain.domain)
        assert address == f"nick@{valid_domain.domain}"

    def test_should_raise_an_error_with_an_invalid_domain(self):
        """It should raise an error with an invalid domain"""
        with pytest.raises(DomainNotAvailableException):
            AccountManager.generate_address(user="nick", domain="invalid.nope")

    def test_should_be_able_to_generate_a_random_password(self):
        """It should be able to generate a random password"""
        password = AccountManager._generate_password(6)
        assert len(password) == 6
        assert type(password) is str

    def test_should_be_able_to_create_an_account_from_a_dict(self):
        """It should be able to create an Account from a dict"""
        data = {"id": "000011",
                "address": "account@testdomain.com",
                "quota": 40000,
                "used": 0,
                "isDisabled": True,
                "isDeleted": False,
                "createdAt": "2021-05-22T00:00:00+00:00",
                "updatedAt": "2021-05-22T00:00:00+00:00",
                "password": "secure"
                }
        account = AccountManager._account_from_dict(data)
        assert isinstance(account, Account)
        assert account.id == data["id"]

    def test_should_be_able_to_create_an_account_with_no_arguments(self):
        """It should be able to create an account with no arguments"""
        account = AccountManager.new()
        assert isinstance(account, Account)
        assert len(account.address) > 0
        assert len(account.password) == 6

    @skip_vcr
    def test_should_be_able_to_create_an_account_with_the_specified_arguments(self):
        """It should be able to create an account with the specified arguments"""
        user = generate_username(1)[0].lower()
        domain = DomainManager.get_active_domains()[0].domain
        password = "secure"
        account = AccountManager.new(user=user, domain=domain, password=password)
        assert isinstance(account, Account)
        assert account.address == f"{user}@{domain}"
        assert account.password == password

    def test_should_pass_along_exception_when_creating_users(self):
        """It should pass along exception when creating users"""
        user = generate_username(1)[0].lower()
        AccountManager.new(user=user)
        with pytest.raises(HTTPError):
            AccountManager.new(user=user)

    def test_should_be_able_to_get_a_jwt(self):
        """It should be able to get a JWT"""
        account = AccountManager.new()
        jwt = AccountManager.get_jwt(account.address, account.password)
        assert type(jwt) is str
        assert len(jwt) > 0

    def test_should_raise_an_exception_when_getting_a_jwt_with_wrong_credentials(self):
        """It should raise an exception when getting a JWT with wrong credentials"""
        with pytest.raises(HTTPError):
            AccountManager.get_jwt("nothere@nothere.not", "nope")

    def test_should_be_able_to_login(self):
        """It should be able to login"""
        account = AccountManager.new()
        logged_account = AccountManager.login(account.address, account.password)
        assert isinstance(logged_account, Account)
        assert logged_account.address == account.address
        assert logged_account.password == account.password
        assert logged_account.createdAt == account.createdAt
        assert logged_account.jwt is not None
        assert len(logged_account.jwt) > 0

    def test_should_raise_an_exception_when_loggin_in_with_the_wrong_credentials(self):
        """It should raise an exception when loggin in with the wrong credentials"""
        account = AccountManager.new()
        with pytest.raises(HTTPError) as err:
            AccountManager.login(account.address, "wrong_pass")
        assert '401 Client Error: Unauthorized' in err.value.args[0]

    def test_can_return_an_account_from_the_id_and_a_jwt(self):
        """It can return an account from the id and a jwt"""
        account = AccountManager.new()
        jwt = AccountManager.get_jwt(account.address, account.password)
        account_data = AccountManager.get_account_data(jwt)
        assert account.id == account_data["id"]
        account_data = AccountManager.get_account_data(jwt, account.id)
        assert account.id == account_data["id"]


@pytest.mark.vcr
class TestAMessage:
    """Test: A Message..."""

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        request.cls.account = AccountManager.new()
        request.cls.account.login()
        request.cls.data = {
            "id": "60bfa3ebf944810cc4987a6a",
            "accountId": "/accounts/60bdfa42aa8bf07f8c2cf886",
            "msgid": "<CADwTKWmdEaO3iBTZwSuVHgBnXt5Aqyc0OHOLVQvwQZpcwF11tg@mail.dummy.com>",
            "from": {
                "address": "sender@dummy.com",
                "name": "nick"
            },
            "to": [
                {
                    "address": "test@logicstreak.com",
                    "name": ""
                }
            ],
            "subject": "Fwd: test",
            "intro": "---------- Forwarded message --------- Da: nick <sender@dummy.com> Date: mar 8 giu 2021 alle ore 19:05 Subject: test To:…",
            "seen": False,
            "isDeleted": False,
            "hasAttachments": False,
            "size": 3566,
            "downloadUrl": "/messages/60bfa3ebf944810cc4987a6a/download",
            "createdAt": "2021-06-08T17:07:07+00:00",
            "updatedAt": "2021-06-08T17:07:55+00:00"
        }
        request.cls.data_full = {
            "id": "60bfa3ebf944810cc4987a6a",
            "accountId": "/accounts/60bdfa42aa8bf07f8c2cf886",
            "msgid": "<CADwTKWmdEaO3iBTZwSuVHgBnXt5Aqyc0OHOLVQvwQZpcwF11tg@mail.dummy.com>",
            "from": {
                "address": "sender@dummy.com",
                "name": "nick"
            },
            "to": [
                {
                    "address": "test@logicstreak.com",
                    "name": ""
                }
            ],
            "cc": [
                {
                    "address": "test2@logicstreak.com",
                    "name": ""
                }
            ],
            "bcc": [],
            "subject": "Fwd: test",
            "seen": False,
            "flagged": False,
            "isDeleted": False,
            "verifications": [],
            "retention": True,
            "retentionDate": "2021-06-15T17:07:55+00:00",
            "text": "---------- Forwarded message ---------\nDa: nick <sender@dummy.com>\nDate: mar 8 giu 2021 alle ore 19:05\nSubject: test\nTo: <test@logisticstreak.com>\n\n\nbanana",
            "html": [
                "<div dir=\"ltr\"><br><br><div class=\"gmail_quote\"><div dir=\"ltr\" class=\"gmail_attr\">---------- Forwarded message ---------<br>Da: <strong class=\"gmail_sendername\" dir=\"auto\">Nick</strong> <span dir=\"auto\">&lt;<a href=\"mailto:sender@dummy.com\">sender@dummy.com</a>&gt;</span><br>Date: mar 8 giu 2021 alle ore 19:05<br>Subject: test<br>To:  &lt;<a href=\"mailto:test@logisticstreak.com\">test@logisticstreak.com</a>&gt;<br></div><br><br><div dir=\"ltr\">banana</div>\r\n</div></div>"
            ],
            "hasAttachments": False,
            "attachments": [
                {
                    "id": "ATTACH000001",
                    "filename": "test_file.txt",
                    "contentType": "text/plain",
                    "disposition": "attachment",
                    "transferEncoding": "base64",
                    "related": False,
                    "size": 1,
                    "downloadUrl": "/messages/60c20b14c139b1f5df8481fa/attachment/ATTACH000001"
                }
            ],
            "size": 3566,
            "downloadUrl": "/messages/60bfa3ebf944810cc4987a6a/download",
            "createdAt": "2021-06-08T17:07:07+00:00",
            "updatedAt": "2021-06-08T17:07:55+00:00"
        }

    def test_should_have_all_required_fields(self):
        """It should have all required fields"""
        data = self.data
        message = Message(
            self.account,
            data["id"],
            data["accountId"],
            data["msgid"],
            data["from"],
            data["to"],
            data["subject"],
            data["seen"],
            data["isDeleted"],
            data["hasAttachments"],
            data["size"],
            data["downloadUrl"],
            data["createdAt"],
            data["updatedAt"],
            intro=data["intro"]
        )
        assert message.account is self.account
        assert message.id == data["id"]
        assert message.accountId == data["accountId"]
        assert message.msgid == data["msgid"]
        assert message.message_from == data["from"]
        assert message.message_to == data["to"]
        assert message.subject == data["subject"]
        assert message.seen == data["seen"]
        assert message.isDeleted == data["isDeleted"]
        assert message.hasAttachments == data["hasAttachments"]
        assert message.size == data["size"]
        assert message.downloadUrl == data["downloadUrl"]
        assert message.createdAt == data["createdAt"]
        assert message.updatedAt == data["updatedAt"]
        assert message.intro == data["intro"]
        assert not message.is_full_message

        data_full = self.data_full
        full_message = Message(
            self.account,
            data_full["id"],
            data_full["accountId"],
            data_full["msgid"],
            data_full["from"],
            data_full["to"],
            data_full["subject"],
            data_full["seen"],
            data_full["isDeleted"],
            data_full["hasAttachments"],
            data_full["size"],
            data_full["downloadUrl"],
            data_full["createdAt"],
            data_full["updatedAt"],
            is_full_message=True,
            cc=data_full["cc"],
            bcc=data_full["bcc"],
            flagged=data_full["flagged"],
            verifications=data_full["verifications"],
            retention=data_full["retention"],
            retentionDate=data_full["retentionDate"],
            text=data_full["text"],
            html=data_full["html"],
            attachments=data_full["attachments"]
        )
        assert full_message.is_full_message
        assert full_message.intro == data["intro"]
        assert full_message.cc == data_full["cc"]
        assert full_message.bcc == data_full["bcc"]
        assert full_message.flagged == data_full["flagged"]
        assert full_message.verifications == data_full["verifications"]
        assert full_message.retention == data_full["retention"]
        assert full_message.retentionDate == data_full["retentionDate"]
        assert full_message.text == data_full["text"]
        assert full_message.html == data_full["html"]
        assert full_message.attachments == data_full["attachments"]

    def test_should_be_able_to_build_a_message_from_a_intro_message_dict(self):
        """It should be able to build a Message from a intro message dict"""
        message = Message._from_intro_dict(self.data, self.account)
        assert isinstance(message, Message)
        assert message.account is self.account
        assert message.id == self.data["id"]
        assert message.intro == self.data["intro"]
        assert not message.is_full_message

    def test_should_be_able_to_build_a_message_from_a_full_message_dict(self):
        """It should be able to build a Message from a full message dict"""
        message = Message._from_full_dict(self.data_full, self.account)
        assert isinstance(message, Message)
        assert message.account is self.account
        assert message.id == self.data_full["id"]
        assert message.text == self.data_full["text"]
        assert message.is_full_message

    @pytest.mark.timeout(30)
    def test_should_have_a_method_to_download_the_full_message_data(self):
        """It should have a method to download the full message data"""
        account = self.account

        send_test_email(account.address)

        messages = []
        while len(messages) == 0:
            sleep(1)
            messages = account.get_all_messages_intro()

        message = messages[0]
        message.get_full_message()
        assert message.is_full_message
        assert message.text is not None
