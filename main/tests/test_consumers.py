import asyncio
from django.contrib.auth.models import Group
from django.test import TestCase
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from main import consumers
from main import factories

class TestConsumers(TestCase):
    def test_chat_between_two_users_works(self):
        def init_db():
            user = factories.UserFactory(
                email="john@bestemails.com",
                first_name="John",
                last_name="Smith",
            )
            order = factories.OrderFactory(user=user)
            cs_user = factories.UserFactory(
                email="customerservice@booktime.domain",
                first_name="Adam",
                last_name="Ford",
                is_staff=True,
            )
            employees, _ = Group.objects.get_or_create(
                name="Employees",
            )
            cs_user.groups.add(employees)

            return user, order, cs_user

        async def test_body():
            user, order, cs_user = await database_sync_to_async(
                init_db
            )()
            communicator = WebsocketCommunicator(
                consumers.ChatConsumer,
                "/ws/customer-service/%d/" % order.id,
            )
            communicator.scope['user'] = user
            communicator.scope['url_route'] = {
                'kwargs': {'order_id': order.id}
            }
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.send_json_to({
                "type": "message",
                "message": "hello customer service",
            }
            )
            await asyncio.sleep(1)
            await cs_communicator.send_json_to(
                {"type": "message", "message": "hello user"}
            )
            self.assertEquals(
                await communicator.receive_json_from(),
                {"type": "chat_join", "username": "John Smith"},
            )
            self.assertEquals(
                await communicator.receive_json_from(),
            {"type": "chat_join", "username": "Adam Ford"},
            )

