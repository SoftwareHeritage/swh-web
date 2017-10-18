Person
^^^^^^

.. http:get:: /browse/person/(person_id)/

    HTML view that displays information regarding a SWH person.

    :param int person_id: the id of a SWH person
    :statuscode 200: no error
    :statuscode 404: requested person can not be found in the SWH archive
