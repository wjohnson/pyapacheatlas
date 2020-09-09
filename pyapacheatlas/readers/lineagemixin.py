import json

from ..core import AtlasEntity, AtlasProcess
from .util import *

class LineageMixIn():
    def _update_entity_and_array(self, entity, mutableOutput):
        """
        Take in an AtlasEntity and list of AtlasEntities.  If the entity
        exists in the mutableOutput, remove the entity from the list and
        merge the incoming entity with the popped entity.  Append that
        merged entity onto the mutableOutput.

        :param entity:
            The entity to look up in the mutableOutput.
        :param mutableOutput:
            A list of Atlas Entities to search through and update if
            `entity` is found.
        :type entity:
            :class:`~pyapacheatlas.core.entity.AtlasEntity`
        :type mutableOutput:
            list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
        """
        if entity in mutableOutput:
            # Assumes things like name, type name, are consistent
            poppable_index = mutableOutput.index(entity)
            popped_target = mutableOutput.pop(poppable_index)
            # Update the newly created entity with the previous versions
            # attributes
            entity.merge(popped_target)
        mutableOutput.append(entity)

    def _add_table_lineage_entity(self, row, header, attributes, mutableOutput):
        """
        Create an AtlasEntity object and add it to the mutableOutput with the
        desired attributes.
        """
        entity = AtlasEntity(
            name=row[header["Table"]],
            typeName=row[header["Type"]],
            # qualifiedName can be overwritten via the attributes
            # functionality
            qualified_name=row[header["Table"]],
            guid=self.guidTracker.get_guid(),
            attributes=attributes,
            classifications=string_to_classification(
                row.get(header["Classifications"]),
                self.config.value_separator
                )
        )

        self._update_entity_and_array(entity, mutableOutput)

        return entity

    def parse_table_lineage(self, json_rows):
        """
        Converts the "tables" information into Atlas Entities for Target,
        Source, and Process types.  Currently only support one target from
        one source.

        :param json_rows:
            A list of dicts that contain the converted tables of your column
            spreadsheet.
        :type json_rows: list(dict(str,str))
        :return:
            A list of atlas entities that represent your source, target,
            and table processes.
        :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)

        """
        # Required attributes
        # NOTE: Classification is not actually required but it's being 
        # included to avoid being roped in as an attribute
        _required_headers = ["Table", "Type", "Classifications"]
        source_header = {k: "{} {}".format(
            self.config.source_prefix, k) for k in _required_headers}
        target_header = {k: "{} {}".format(
            self.config.target_prefix, k) for k in _required_headers}
        process_header = {k: "{} {}".format(
            self.config.process_prefix, k) for k in ["Name", "Type"]}

        # Read in all Source and Target entities
        output = list()  # TODO: Change to a dict to facilitate lookups
        for row in json_rows:
            # Set up defaults
            target_entity, source_entity, process_entity = None, None, None

            # Always expecting a TARGET in the sheet
            target_attributes = columns_matching_pattern(
                row, self.config.target_prefix,
                does_not_match=list(target_header.values())
            )
            target_entity = self._add_table_lineage_entity(
                row, target_header, target_attributes, output
            )

            if row[source_header["Table"]] is not None:
                # There is a source table
                source_attributes = columns_matching_pattern(
                    row, self.config.source_prefix,
                    does_not_match=list(source_header.values())
                )
                source_entity = self._add_table_lineage_entity(
                    row, source_header, source_attributes, output
                )

            # Map the source and target tables to a process
            if row[process_header["Name"]] is not None:
                # There is a process
                inputs_to_process = [] if source_entity is None else [
                    source_entity.to_json(minimum=True)]
                process_attributes = columns_matching_pattern(
                    row, self.config.process_prefix,
                    does_not_match=list(process_header.values())
                )

                process_entity = AtlasProcess(
                    name=row[process_header["Name"]],
                    typeName=row[process_header["Type"]],
                    qualified_name=row[process_header["Name"]],
                    guid=self.guidTracker.get_guid(),
                    inputs=inputs_to_process,
                    outputs=[target_entity.to_json(minimum=True)],
                    attributes=process_attributes
                )
                
                self._update_entity_and_array(process_entity, output)

        # Return all entities
        return output

    def parse_column_lineage(self, json_rows, atlas_entities, atlas_typedefs, use_column_mapping=False):
        """
        :param json_rows:
            A list of dicts that contain the converted rows of your column
            spreadsheet.
        :type json_rows: list(dict(str,str))
        :param atlas_entities:
            A list of :class:`~pyapacheatlas.core.entity.AtlasEntity`
            containing the referred entities.
        :type atlas_entities: 
            list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
        :param dict(str,list(dict)) atlas_typedefs:
            The results of requesting all type defs from Apache Atlas, 
            including entityDefs, relationshipDefs, etc.  relationshipDefs
            are the only values used.
        :param bool use_column_mapping:
            Should the table processes include the columnMappings attribute
            that represents Column Lineage in Azure Data Catalog.
            Defaults to False.
        :return:
            A list of atlas entities that represent your column source, target,
            and column lineage processes.
        :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)

        """
        # Required attributes
        # NOTE: Classification is not actually required but it's being 
        # included to avoid being roped in as an attribute
        _required_headers = ["Table", "Column", "Classifications"]
        source_header = {k: "{} {}".format(
            self.config.source_prefix, k) for k in _required_headers}
        target_header = {k: "{} {}".format(
            self.config.target_prefix, k) for k in _required_headers}
        process_header = {k: "{} {}".format(
            self.config.target_prefix, k) for k in ["Name", "Type"]}

        transformation_column_header = self.config.column_transformation_name
        # No required process headers

        output = []
        # `tables` Stores all of the table entities by their name seen in the 
        # loop for faster lookup
        tables = {}  
        # table_process_guid: 
        # {"input_table":"","output_table":"","columnMapping":[]}
        dataset_mapping = {}
        # Caches all of the table processes seen in the loop for faster lookup
        table_and_proc_mappings = {}

        for row in json_rows:
            # Set up defaults
            target_entity, source_entity, process_entity = None, None, None
            target_entity_table_name, source_entity_table_name = None, None
            # Given the existing table entity in atlas_entities,
            # look up the appropriate column type
            target_entity_table_name = row[target_header["Table"]]
            if target_entity_table_name not in tables:
                target_table_entity = first_entity_matching_attribute(
                    "name", target_entity_table_name, atlas_entities)
                tables[target_entity_table_name] = target_table_entity

            columns_relationship = first_relationship_that_matches(
                end_def="endDef1",
                end_def_type=target_table_entity.typeName,
                end_def_name="columns",
                relationship_typedefs=atlas_typedefs["relationshipDefs"]
            )
            target_col_type = columns_relationship["endDef2"]["type"]

            # There should always be a target
            target_entity = AtlasEntity(
                name=row[target_header["Column"]],
                typeName=target_col_type,
                # qualifiedName can be overwritten via the attributes 
                # functionality
                qualified_name=target_entity_table_name + \
                "#" + row[target_header["Column"]],
                guid=self.guidTracker.get_guid(),
                attributes=columns_matching_pattern(
                    row, self.config.target_prefix, 
                    does_not_match=list(target_header.values())
                ),
                # TODO: Make the relationship name dynamic instead of only table
                relationshipAttributes={
                    "table": tables[target_entity_table_name].to_json(minimum=True)},
                classifications=string_to_classification(
                    row.get(target_header["Classifications"]))
            )
            if target_entity in output:
                poppable_index = output.index(target_entity)
                popped_target = output.pop(poppable_index)
                target_entity.merge(popped_target)
            # Add to outputs
            output.append(target_entity)

            # Source Column is optiona in the spreadsheet
            if row[source_header["Table"]] is not None:
                # Given the existing source table entity in atlas_entities,
                # look up the appropriate column type
                source_entity_table_name = row[source_header["Table"]]

                if source_entity_table_name not in tables:
                    source_table_entity = first_entity_matching_attribute(
                        "name", source_entity_table_name, atlas_entities)
                    tables[source_entity_table_name] = source_table_entity

                columns_relationship_source = first_relationship_that_matches(
                    end_def="endDef1",
                    end_def_type=source_table_entity.typeName,
                    end_def_name="columns",
                    relationship_typedefs=atlas_typedefs["relationshipDefs"]
                )
                source_col_type = columns_relationship_source["endDef2"]["type"]

                source_entity = AtlasEntity(
                    name=row[source_header["Column"]],
                    typeName=source_col_type,
                    # qualifiedName can be overwritten via the attributes functionality
                    qualified_name=source_entity_table_name + \
                    "#" + row[source_header["Column"]],
                    guid=self.guidTracker.get_guid(),
                    attributes=columns_matching_pattern(
                        row, self.config.source_prefix, does_not_match=list(source_header.values())),
                    # TODO: Make the relationship name more dynamic instead of hard coding query
                    relationshipAttributes={
                        "table": tables[source_entity_table_name].to_json(minimum=True)},
                    classifications=string_to_classification(
                        row.get(source_header["Classifications"]))
                )
                if source_entity in output:
                    poppable_index = output.index(source_entity)
                    popped_source = output.pop(poppable_index)
                    source_entity.merge(popped_source)
                # Add to outputs
                output.append(source_entity)

            # Given the existing process that with target table and source
            # table types, look up the appropriate column_lineage type
            # LIMITATION: Prevents you from specifying multiple processes 
            # for the same input and output tables
            try:
                table_process = first_process_containing_io(
                    source_entity_table_name, target_entity_table_name, atlas_entities)
            except ValueError as e:
                # ValueError means we didn't find anything that matched
                # Try using a wildcard search if the source entity is none
                # to match to any process that at least includes the target
                # entity table
                if source_entity_table_name is None:
                    table_process = first_process_containing_io(
                        "*", target_entity_table_name, atlas_entities)
                else:
                    raise e

            if table_process.get_name() in table_and_proc_mappings:
                process_type = table_and_proc_mappings[table_process.get_name(
                )]["column_lineage_type"]
            else:
                process_type = from_process_lookup_col_lineage(
                    table_process.get_name(),
                    atlas_entities,
                    atlas_typedefs["relationshipDefs"]
                )
                table_and_proc_mappings[table_process.get_name()] = {
                    "column_lineage_type": process_type
                }

            # Assuming there is always a Process for adding at least the
            # target table
            process_attributes = columns_matching_pattern(
                row, self.config.process_prefix)
            process_attributes.update({"dependencyType": "SIMPLE"})
            if row[transformation_column_header] is not None:
                process_attributes.update(
                    {"dependencyType": "EXPRESSION", 
                    "expression": row[transformation_column_header]
                })

            process_entity = AtlasProcess(
                name=table_process.get_name(),
                typeName=process_type,
                # qualifiedName can be overwritten via the attributes functionality
                qualified_name=table_process.get_name() + "@derived_column:{}".format(
                    target_entity.get_name()
                ),
                guid=self.guidTracker.get_guid(),
                # Assuming always a single output
                inputs=[] if source_entity is None else [
                    source_entity.to_json(minimum=True)],
                outputs=[target_entity.to_json(minimum=True)],
                attributes=process_attributes,
                # TODO: Make the relationship name more dynamic instead of hard coding query
                relationshipAttributes={
                    "query": table_process.to_json(minimum=True)}
            )
            if process_entity in output:
                poppable_index = output.index(process_entity)
                popped_process = output.pop(poppable_index)
                process_entity.merge(popped_process)
            output.append(process_entity)

            if use_column_mapping:
                # Handles multiple source columns from multiple source datasets
                col_map_source_col = "*" if source_entity is None else source_entity.get_name()
                col_map_target_col = target_entity.get_name()
                col_map_source_table = row[source_header["Table"]] or "*"
                col_map_target_table = row[target_header["Table"]]
                hash_key = hash(col_map_source_table + col_map_target_table)
                col_map_dict = {"Source": col_map_source_col,
                                "Sink": col_map_target_col}
                data_map_dict = {"Source": col_map_source_table,
                                "Sink": col_map_target_table}

                if table_process.guid in dataset_mapping:
                    if hash_key in dataset_mapping[table_process.guid]:
                        # Hash Key has not been seen before
                        dataset_mapping[table_process.guid][hash_key]["ColumnMapping"].append(
                            col_map_dict)
                    else:
                        # Hash key has been seen before
                        dataset_mapping[table_process.guid][hash_key] = {
                            "ColumnMapping": [col_map_dict],
                            "DatasetMapping": data_map_dict
                        }
                else:
                    # This guid has never been seen before
                    dataset_mapping[table_process.guid] = {
                        hash_key: {
                            "ColumnMapping": [col_map_dict],
                            "DatasetMapping": data_map_dict
                        }
                    }
        # Update the passed in atlas_entities if we are using column mapping
        if use_column_mapping:
            for entity in atlas_entities:
                if entity.guid in dataset_mapping:
                    # hash_key: {DSMap:{}, ColumnMapping}
                    column_mapping_attribute = [
                        mappings for mappings in dataset_mapping[entity.guid].values()]
                    entity.attributes.update(
                        {"columnMapping": json.dumps(column_mapping_attribute)}
                    )

        return output
