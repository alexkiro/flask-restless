# -*- coding: utf-8; Mode: Python -*-
#
# Copyright 2012 Jeffrey Finkelstein <jefrey.finkelstein@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Unit tests for the :mod:`flaskext.restless.manager` module."""
from json import dumps
from json import loads
import os
from tempfile import mkstemp
import unittest

from elixir import create_all
from elixir import drop_all
from elixir import session
from flask import Flask
from sqlalchemy import create_engine

from flaskext.restless.manager import APIManager
from .models import setup
from .models import Person


class APIManagerTest(unittest.TestCase):
    """Unit tests for the :class:`flaskext.restless.manager.APIManager` class.

    """

    def setUp(self):
        """Creates the database, :class:`~flask.Flask` object, and the
        :class:`~flaskext.restless.manager.APIManager` for that application.

        """
        # set up the database
        self.db_fd, self.db_file = mkstemp()
        setup(create_engine('sqlite:///%s' % self.db_file))
        create_all()
        session.commit()
        
        # set up the application and API manager
        app = Flask(__name__)
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.manager = APIManager(app)

    def tearDown(self):
        """Drops all tables from the temporary database and closes and unlink
        the temporary file in which it lived.

        """
        drop_all()
        session.commit()
        os.close(self.db_fd)
        os.unlink(self.db_file)

    def test_create_api(self):
        """Tests that the
        :meth:`flaskext.restless.manager.APIManager.create_api` method creates
        endpoints which are accessible by the client, only allow specified HTTP
        methods, and which provide a correct API to a database.

        """
        # create three different APIs for the same model
        # TODO note in documentation that only
        self.manager.create_api(Person, methods=['GET', 'POST'])
        self.manager.create_api(Person, methods=['PATCH'], url_prefix='/api2')
        self.manager.create_api(Person, methods=['GET'],
                                url_prefix='/readonly')

        # test that specified endpoints exist
        response = self.app.post('/api/Person', data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(loads(response.data)['id'], 1)
        response = self.app.get('/api/Person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)

        # test that non-specified methods are not allowed
        response = self.app.delete('/api/Person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.patch('/api/Person/1',
                                  data=dumps(dict(name='bar')))
        self.assertEqual(response.status_code, 405)

        # test that specified endpoints exist
        response = self.app.patch('/api2/Person/1',
                                  data=dumps(dict(name='bar')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['id'], 1)
        self.assertEqual(loads(response.data)['name'], 'bar')

        # test that non-specified methods are not allowed
        response = self.app.get('/api2/Person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.delete('/api2/Person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.post('/api2/Person',
                                 data=dumps(dict(name='baz')))
        self.assertEqual(response.status_code, 405)

        # test that the model is the same as before
        response = self.app.get('/readonly/Person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)
        self.assertEqual(loads(response.data)['objects'][0]['name'], 'bar')
