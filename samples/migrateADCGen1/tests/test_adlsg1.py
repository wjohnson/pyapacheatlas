import sys
sys.path.append("./")
from mappers.adlsg1 import ADLSGen1Directory
from mappers.adlsg1 import ADLSGen1DataLake



CORE_TERMS = {"TERMID123": "term123@Glossary"}


DL_ENTITY = {
    "content": {
        "properties": {
            "dsl": {
                "address": {
                    "url": "https://datalake1.azuredatalakestore.net/"
                },
                "protocol": "webhdfs",
                "authentication": "oauth"
            },
            "dataSource": {
                "sourceType": "Azure Data Lake Store",
                "objectType": "Data Lake"
            }
        }
    }
}


DIR_ENTITY = {
    "content": {
        "properties": {
            "dsl": {
                "address": {
                    "url": "https://datalake1.azuredatalakestore.net/folder/file"
                },
                "protocol": "webhdfs",
                "authentication": "oauth"
            },
            "dataSource": {
                "sourceType": "Azure Data Lake Store",
                "objectType": "Directory"
            }
        }
    }
}


dl = ADLSGen1DataLake(DL_ENTITY, CORE_TERMS)
directory = ADLSGen1Directory(DIR_ENTITY, CORE_TERMS)


def test_adls_qualified_nameDL():
    assert(dl.qualified_name() ==
           "adl://datalake1.azuredatalakestore.net")


def test_adls_qualified_nameDirectory():
    assert(directory.qualified_name() ==
           "adl://datalake1.azuredatalakestore.net/folder/file")
#https://aaganalyticsprodlake1.azuredatalakestore.net/webhdfs/v1/raw/guest/online-exp/omniture/data/webcheckin #pulled from alaska