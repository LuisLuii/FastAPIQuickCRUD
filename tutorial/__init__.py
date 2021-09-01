from collections import defaultdict

a = [
    {
        "id": 1,
        "id_foreign": {
            "id": 1,
            "parent_id": 1
        }
    },
    {
        "id": 1,
        "id_foreign": {
            "id": 2,
            "parent_id": 1
        }
    },
    {
        "id": 1,
        "id_foreign": {
            "id": 3,
            "parent_id": 1
        }
    },
    {
        "id": 2,
        "id_foreign": {
            "id": 4,
            "parent_id": 2
        }
    },
    {
        "id": 2,
        "id_foreign": {
            "id": 5,
            "parent_id": 2
        }
    },
    {
        "id": 2,
        "id_foreign": {
            "id": 6,
            "parent_id": 2
        }
    }
]


b = [
    {"id": 1,
     "id_foreign":[{
             "id": 3,
             "parent_id": 1
         }, {
             "id": 1,
             "parent_id": 1
         }, {"id": 2,
             "parent_id": 1}
         ],
     },
    {"id": 2,
     "id_foreign": [{
         "id": 4,
         "parent_id": 2
     }, {
         "id": 5,
         "parent_id": 2
     }, {
         "id": 6,
         "parent_id": 2}
        ]
     }
]
tmp = defaultdict(list)
print(tmp)
from itertools import groupby
def test(*args, **kwargs):
    tmp = {}
    for k, v in args[0].items():
        if '_foreign' not in k:
            tmp[k] = v
    return tmp

response_list = []
for key, group in groupby(a, test):
    response = {}
    for i in group:
        for k , v in i.items():
            if '_foreign' in k:
                if k not in response:
                    response[k] = [v]
                else:
                    response[k].append(v)
        for response_ in response:
            i.pop(response_, None)
        result = i | response
    response_list.append(result)
print()
# result = []
# for data_index in range(0, len(a)):
#     for data_index_ in range(0, len(a)):
#         foreign_ = {}
#         non_foreign_ = {}
#         for k, v in a[data_index].items():
#             tmp = {}
#             if '_foreign' in k:
#                 foreign_[k] = v
#             else:
#                 non_foreign_[k] = v
#
#         foreign__ = {}
#         non_foreign__ = {}
#         for k, v in a[data_index_].items():
#             tmp = {}
#             if '_foreign' in k:
#                 foreign__[k] = v
#             else:
#                 non_foreign__[k] = v
#         if non_foreign_ == non_foreign__:
#             print(data_index)
#             print(data_index_)
#         print('----')
#     print('===')