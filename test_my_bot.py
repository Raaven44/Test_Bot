import os
import sys
import logging
import unittest
import shutil
from telebot import types


from datetime import datetime
import pytest
from unittest import mock
from peewee import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import clear_
from main import start_, User, DoesNotExist
from main import help_
from main import list_, Subscriptions, bot
from main import Search
from main import add_
from main import hour_
from main import send_news_

def test_clear_(mock_message):
    mock_message = mock.MagicMock()  

    with mock.patch('main.User.get_by_id') as mock_get_by_id, \
            mock.patch('main.Subscriptions.delete') as mock_delete, \
            mock.patch('main.bot.send_message') as mock_send_message:
        
        mock_get_by_id.return_value = User()

        clear_(mock_message)

        mock_get_by_id.assert_called_once_with(mock_message.from_user.id)
        mock_delete.assert_called_once()
        mock_send_message.assert_called_once_with(mock_message.from_user.id, 'Список Ваших подписок очищен')





def test_help_(mock_message):
    with mock.patch('main.bot.send_message') as mock_send_message:
        help_(mock_message)
        mock_send_message.assert_called_once_with(
            chat_id=mock_message.from_user.id,
            text=mock.ANY,
            parse_mode='MarkdownV2'
        )

@pytest.fixture
def mock_message():
    return mock.Mock()


def test_list_(mock_message):
    
    mock_subscription = mock.Mock()
    mock_subscription.search.text = 'Test'
    mock_subscriptions = [mock_subscription]
    mock_user = mock.Mock()

   
    mock_message.from_user.id = 123

  
    with mock.patch('main.Subscriptions.select') as mock_select, \
            mock.patch('main.User.get_by_id', return_value=mock_user) as mock_get_by_id, \
            mock.patch.object(bot, 'send_message') as mock_send_message:
       
        mock_query = mock.Mock()
        mock_query.where.return_value = mock_subscriptions
        mock_select.return_value = mock_query

        list_(mock_message)

    mock_get_by_id.assert_called_once_with(pk=mock_message.from_user.id)
    mock_select.assert_called_once()
    mock_query.where.assert_called_once_with(Subscriptions.user == mock_user)
    mock_send_message.assert_called_once_with(mock_message.from_user.id, 'Ваши подписки:\n1. Test\n')


def test_add_(mock_message):
    mock_message.text = '/add Test'

    
    mock_search = mock.Mock()
    mock_search.text = 'Test'
    mock_user = mock.Mock()
    mock_subscription = mock.Mock(spec=Subscriptions)

  
    with mock.patch('main.Search.get', return_value=mock_search) as mock_search_get, \
            mock.patch('main.User.get_by_id', return_value=mock_user), \
            mock.patch('main.Subscriptions.select') as mock_select, \
            mock.patch('main.Subscriptions.create') as mock_create, \
            mock.patch.object(bot, 'send_message') as mock_send_message:

        mock_select.return_value.where.return_value.exists.return_value = False

        add_(mock_message)

        
        mock_search_get.assert_called_once_with(Search.text == 'Test')
        mock_select.assert_called_once()
        mock_create.assert_called_once_with(user=mock_user, search=mock_search)
        mock_send_message.assert_called_once()


@pytest.fixture
def user():
    
    user = User.create(id=123456789, hour=0)
    yield user
    
    user.delete_instance()

database = SqliteDatabase('news.db')
User._meta.database = database


def test_hour_():
    
    user = User.create(id=123456789, hour=0, vip=False)

    hour_(MockMessage(text='/hour 10'))
    updated_user = User.get(User.id == 123456789)
    assert updated_user.hour == 10

    
    message = MockMessage(text='/hour')
    hour_(message)
    assert message.sent_message == 'Поисковые запросы приходят в 10-м часу'

  
    message = MockMessage(text='/hour 30')
    hour_(message)
    assert message.sent_message == 'Нужно ввести значение от 0 до 23 включительно.'

    
    message = MockMessage(text='/hour abc')
    hour_(message)
    assert message.sent_message == 'Час должен быть указан как целое число в диапазоне от 0 до 23 включительно.'


class MockMessage:
    def __init__(self, text):
        self.text = text
        self.sent_message = None

    def send_message(self, chat_id, text):
        self.sent_message = text


def test_send_news_():
    with mock.patch('main.bot.send_message') as mock_send_message:
        send_news_(123456789, 'Новости', 'https://example.com/news')
        mock_send_message.assert_called_once_with(123456789, 'Подписка: Новости\nhttps://example.com/news')

shutil.copyfile('news.db', 'test_news.db')


test_db = SqliteDatabase(':memory:')
User._meta.database = test_db
Search._meta.database = test_db
Subscriptions._meta.database = test_db


def create_test_data():
    test_user = User.create(id=1, hour=10)
    test_search = Search.create(text='test search')
    Subscriptions.create(user=test_user, search=test_search)

class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        
        User.create_table()
        Search.create_table()
        Subscriptions.create_table()
        create_test_data()

    def tearDown(self):
       
        User.drop_table()
        Search.drop_table()
        Subscriptions.drop_table()

    def test_add_subscription(self):
       
        test_user = User.get_by_id(1)
        test_search = Search.create(text='new search')
        Subscriptions.create(user=test_user, search=test_search)

       
        subscription_count = Subscriptions.select().where(Subscriptions.user == test_user).count()
        self.assertEqual(subscription_count, 2)

    def test_delete_subscription(self):
        
        test_user = User.get_by_id(1)
        test_search = Search.get(Search.text == 'test search')
        Subscriptions.delete().where(Subscriptions.user == test_user, Subscriptions.search == test_search).execute()

       
        subscription_count = Subscriptions.select().where(Subscriptions.user == test_user).count()
        self.assertEqual(subscription_count, 0)

if __name__ == '__main__':
    pytest.main([__file__])












