
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.base import DataType, DictReference, NullListReference, Reference
from jmapy.orm.changes import ChangableData
from jmapy.orm.filtering import FilterCondition, or_
from jmapy.orm.get import GettableData
from jmapy.orm.query import QueryableData
from jmapy.orm.query_changes import QueryChangableData
from jmapy.orm.set import SettableData
from tests.util import dump_exec


class Todo(
    QueryableData,
    GettableData,
    SettableData,
    ChangableData,
    QueryChangableData,
    DataType
):
    id: Reference[Self, str] = Reference[Self, str](init=False)
    title: Reference[Self, str] = Reference[Self, str]()
    keywords: DictReference[Self, str, bool] = DictReference[Self, str, bool](default_factory=list)
    neural_network_time_estimation: Reference[Self, int] = Reference[Self, int](init=False)
    sub_todo_ids: NullListReference[Self, ID] = NullListReference[Self, ID](default=None)

    @staticmethod
    def has_keyword(keyword: str) -> FilterCondition:
        return FilterCondition(
            "hasKeyword",
            keyword
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            **({"keywords": self.keywords} if self.keywords else {}),
            **({"SubTodoIds": self.sub_todo_ids} if self.sub_todo_ids else {})
        }

    
def test_keyword_match():
    request = dump_exec(
        Todo.query(
            "x",
            or_(
                Todo.has_keyword("music"),
                Todo.has_keyword("video")
            ),
            [Todo.title],
            position = 0,
            limit = 10
        ).then(
        lambda query: Todo.get(
            "x",
            query.ids
        )
        )
    )
    
    query_call_id = request[0][2]
    get_call_id = request[1][2]

    assert request ==  [( "Todo/query", {
                     "accountId": "x",
                     "filter": {
                       "operator": "OR",
                       "conditions": [
                         { "hasKeyword": "music" },
                         { "hasKeyword": "video" }
                       ]
                     },
                     "sort": [{ "property": "title" }],
                     "position": 0,
                     "limit": 10
                   }, query_call_id ),
                   ( "Todo/get", {
                     "accountId": "x",
                     "#ids": {
                       "resultOf": query_call_id,
                       "name": "Todo/query",
                       "path": "/ids"
                     }
                   }, get_call_id )]


def test_todo_set():
    request = dump_exec(
        Todo.set(
            "x",
            if_in_state="10324",
            update={
                "a": {
                    Todo.id: "a",
                    Todo.title: "Practise Piano",
                    Todo.keywords: {
                         "music": True,
                         "beethoven": True,
                         "chopin": True,
                         "liszt": True,
                         "rachmaninov": True
                       },
                    Todo.neural_network_time_estimation: 360
                }
            }
        )
    )

    call_set_id = request[0][2]

    assert request == [( "Todo/set", {
                    "accountId": "x",
                    "ifInState": "10324",
                    "update": {
                        "a": {
                        "id": "a",
                        "title": "Practise Piano",
                        "keywords": {
                            "music": True,
                            "beethoven": True,
                            "chopin": True,
                            "liszt": True,
                            "rachmaninov": True
                        },
                        "neuralNetworkTimeEstimation": 360
                        }
                    }
                    }, call_set_id )]

def test_todo_create():
    request = dump_exec(
        Todo.set(
            "x",
            create={
                "k15": Todo(title="Warm up with scales")
            },
            update={
                "a": {
                    Todo.sub_todo_ids: ["#k15"]
                }
            }
        )
    )

    call_set_id = request[0][2]

    assert request == [( "Todo/set", {
                     "accountId": "x",
                     "create": {
                       "k15": {
                         "title": "Warm up with scales"
                       }
                     },
                     "update": {
                       "a": {
                         "subTodoIds": [ "#k15" ]
                       }
                     }
                   }, call_set_id )]

def test_todo_changes():
    request = dump_exec(
        Todo.changes(
            "x",
            "10324",
            50
        ).then(
            Todo.query_changes(
            "x",
            filter=or_(
                Todo.has_keyword("music"),
                Todo.has_keyword("video")
            ),
            sort=[Todo.title],
            since_query_state="y13213",
            max_changes=50
        )
        )
    )

    call_changes_id = request[0][2]
    call_qc_id = request[1][2]

    assert request == [( "Todo/changes", {
                     "accountId": "x",
                     "sinceState": "10324",
                     "maxChanges": 50
                   }, call_changes_id ),
                   ( "Todo/queryChanges", {
                     "accountId": "x",
                     "filter": {
                       "operator": "OR",
                       "conditions": [
                         { "hasKeyword": "music" },
                         { "hasKeyword": "video" }
                       ]
                     },
                     "sort": [{ "property": "title" }],
                     "sinceQueryState": "y13213",
                     "maxChanges": 50
                   }, call_qc_id )]
