"""
    tests.test_deleting
    ~~~~~~~~~~~~~~~~~~~

    Provides tests for deleting resources from endpoints generated by
    Flask-Restless.

    This module includes tests for additional functionality that is not already
    tested by :mod:`test_jsonapi`, the module that guarantees Flask-Restless
    meets the minimum requirements of the JSON API specification.

    :copyright: 2015 Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com> and
                contributors.
    :license: GNU AGPLv3+ or BSD

"""
from flask import json
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode

from flask.ext.restless import CONTENT_TYPE

from .helpers import dumps
from .helpers import loads
from .helpers import ManagerTestBase
from .helpers import MSIE8_UA
from .helpers import MSIE9_UA


class TestDeleting(ManagerTestBase):
    """Tests for deleting resources."""

    def setUp(self):
        """Creates the database, the :class:`~flask.Flask` object, the
        :class:`~flask_restless.manager.APIManager` for that application, and
        creates the ReSTful API endpoints for the :class:`TestSupport.Person`
        and :class:`TestSupport.Article` models.

        """
        super(TestDeleting, self).setUp()

        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)

        self.Person = Person
        self.Base.metadata.create_all()
        self.manager.create_api(Person, methods=['DELETE'])

    def tearDown(self):
        """Drops all tables from the temporary database."""
        self.Base.metadata.drop_all()

    def test_correct_content_type(self):
        """Tests that the server responds with :http:status:`201` if the
        request has the correct JSON API content type.

        """
        person = self.Person(id=1)
        self.session.add(person)
        self.session.commit()
        response = self.app.delete('/api/person/1', content_type=CONTENT_TYPE)
        assert response.status_code == 204
        assert response.headers['Content-Type'] == CONTENT_TYPE

    def test_no_content_type(self):
        """Tests that the server responds with :http:status:`415` if the
        request has no content type.

        """
        person = self.Person(id=1)
        self.session.add(person)
        self.session.commit()
        response = self.app.delete('/api/person/1', content_type=None)
        assert response.status_code == 415
        assert response.headers['Content-Type'] == CONTENT_TYPE

    def test_wrong_content_type(self):
        """Tests that the server responds with :http:status:`415` if the
        request has the wrong content type.

        """
        person = self.Person(id=1)
        self.session.add(person)
        self.session.commit()
        bad_content_types = ('application/json', 'application/javascript')
        for content_type in bad_content_types:
            response = self.app.delete('/api/person/1',
                                       content_type=content_type)
            assert response.status_code == 415
            assert response.headers['Content-Type'] == CONTENT_TYPE

    def test_msie8(self):
        """Tests for compatibility with Microsoft Internet Explorer 8.

        According to issue #267, making requests using JavaScript from MSIE8
        does not allow changing the content type of the request (it is always
        ``text/html``). Therefore Flask-Restless should ignore the content type
        when a request is coming from this client.

        """
        person = self.Person(id=1)
        self.session.add(person)
        self.session.commit()
        headers = {'User-Agent': MSIE8_UA}
        content_type = 'text/html'
        response = self.app.delete('/api/person/1', headers=headers,
                                   content_type=content_type)
        assert response.status_code == 204

    def test_msie9(self):
        """Tests for compatibility with Microsoft Internet Explorer 9.

        According to issue #267, making requests using JavaScript from MSIE9
        does not allow changing the content type of the request (it is always
        ``text/html``). Therefore Flask-Restless should ignore the content type
        when a request is coming from this client.

        """
        person = self.Person(id=1)
        self.session.add(person)
        self.session.commit()
        headers = {'User-Agent': MSIE9_UA}
        content_type = 'text/html'
        response = self.app.delete('/api/person/1', headers=headers,
                                   content_type=content_type)
        assert response.status_code == 204

    def test_disallow_delete_many(self):
        """Tests that deleting an entire collection is disallowed by default.

        Deleting an entire collection is not discussed in the JSON API
        specification.

        """
        response = self.app.delete('/api/person')
        assert response.status_code == 405

    def test_delete_collection(self):
        """Tests for deleting all instances of a collection.

        Deleting an entire collection is not discussed in the JSON API
        specification.

        """
        self.session.add_all(self.Person() for n in range(3))
        self.session.commit()
        self.manager.create_api(self.Person, methods=['DELETE'],
                                allow_delete_many=True, url_prefix='/api2')
        response = self.app.delete('/api2/person')
        assert response.status_code == 204
        assert self.session.query(self.Person).count() == 0

    def test_delete_many_filtered(self):
        """Tests for deleting instances of a collection selected by filters.

        Deleting from a collection is not discussed in the JSON API
        specification.

        """
        person1 = self.Person(id=1)
        person2 = self.Person(id=2)
        person3 = self.Person(id=3)
        self.session.add_all([person1, person2, person3])
        self.session.commit()
        self.manager.create_api(self.Person, methods=['DELETE'],
                                allow_delete_many=True, url_prefix='/api2')
        filters = [dict(name='id', op='lt', val=3)]
        url = '/api2/person?filter[objects]={0}'.format(dumps(filters))
        response = self.app.delete(url)
        print(response.data)
        assert response.status_code == 204
        assert [person3] == self.session.query(self.Person).all()

    def test_delete_integrity_error(self):
        """Tests that an :exc:`IntegrityError` raised in a
        :http:method:`delete` request is caught and returned to the client
        safely.

        """
        assert False, 'Not implemented'

    def test_delete_absent_instance(self):
        """Test that deleting an instance of the model which does not exist
        fails.

        This should give us a 404 when the object is not found.

        """
        response = self.app.delete('/api/person/1')
        assert response.status_code == 404

    # TODO tested elsewhere
    #
    # def test_delete_from_relation(self):
    #     """Tests that a :http:method:`delete` request to a related instance
    #     removes that related instance from the specified model.

    #     See issue #193.

    #     """
    #     person = self.Person()
    #     computer = self.Computer()
    #     person.computers.append(computer)
    #     self.session.add_all((person, computer))
    #     self.session.commit()
    #     # Delete the related computer.
    #     response = self.app.delete('/api/person/1/computers/1')
    #     assert response.status_code == 204
    #     # Check that it is actually gone from the relation.
    #     response = self.app.get('/api/person/1')
    #     assert response.status_code == 200
    #     assert len(loads(response.data)['computers']) == 0
    #     # Check that the related instance hasn't been deleted from the database
    #     # altogether.
    #     response = self.app.get('/api/computer/1')
    #     assert response.status_code == 200

    #     # # Add the computer back in to the relation and use the Delete-Orphan
    #     # # header to instruct the server to delete the orphaned computer
    #     # # instance.
    #     # person.computers.append(computer)
    #     # self.session.commit()
    #     # response = self.app.delete('/api/person/1/computers/1',
    #     #                            headers={'Delete-Orphan': 1})
    #     # assert response.status_code == 204
    #     # response = self.app.get('/api/person/1/computers')
    #     # assert response.status_code == 200
    #     # assert len(loads(response.data)['computers']) == 0
    #     # response = self.app.get('/api/computers')
    #     # assert response.status_code == 200
    #     # assert len(loads(response.data)['objects']) == 0
