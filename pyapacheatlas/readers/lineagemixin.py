from collections import OrderedDict
import json
import warnings

from ..core import AtlasEntity, AtlasProcess
from . import util as reader_util


class LineageMixIn():
    """
    A MixIn to support the :class:`~pyapacheatlas.readers.reader.Reader` with
    the table and column level lineages.
    """

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
            name=row[header["table"]],
            typeName=row[header["type"]],
            # qualifiedName can be overwritten via the attributes
            # functionality
            qualified_name=row[header["table"]],
            guid=self.guidTracker.get_guid(),
            attributes=attributes,
            classifications=reader_util.string_to_classification(
                row.get(header["classifications"]),
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
        _required_headers = ["table", "type", "classifications"]
        source_header = {k: "{} {}".format(
            self.config.source_prefix, k) for k in _required_headers}
        target_header = {k: "{} {}".format(
            self.config.target_prefix, k) for k in _required_headers}
        process_header = {k: "{} {}".format(
            self.config.process_prefix, k) for k in ["name", "type"]}

        # Read in all Source and Target entities
        output = list()  # TODO: Change to a dict to facilitate lookups
        for row in json_rows:
            # Set up defaults
            target_entity, source_entity, process_entity = None, None, None

            # Always expecting a TARGET in the sheet
            target_attributes = reader_util.columns_matching_pattern(
                row, self.config.target_prefix,
                does_not_match=list(target_header.values())
            )
            target_entity = self._add_table_lineage_entity(
                row, target_header, target_attributes, output
            )

            if row[source_header["table"]] is not None:
                # There is a source table
                source_attributes = reader_util.columns_matching_pattern(
                    row, self.config.source_prefix,
                    does_not_match=list(source_header.values())
                )
                source_entity = self._add_table_lineage_entity(
                    row, source_header, source_attributes, output
                )

            # Map the source and target tables to a process
            if row[process_header["name"]] is not None:
                # There is a process
                inputs_to_process = [] if source_entity is None else [
                    source_entity.to_json(minimum=True)]
                process_attributes = reader_util.columns_matching_pattern(
                    row, self.config.process_prefix,
                    does_not_match=list(process_header.values())
                )

                process_entity = AtlasProcess(
                    name=row[process_header["name"]],
                    typeName=row[process_header["type"]],
                    qualified_name=row[process_header["name"]],
                    guid=self.guidTracker.get_guid(),
                    inputs=inputs_to_process,
                    outputs=[target_entity.to_json(minimum=True)],
                    attributes=process_attributes
                )

                self._update_entity_and_array(process_entity, output)

        # Return all entities
        return output

    def _update_parent_table_cache(self, parent_table_name, known_tables, atlas_entities):
        """
        Updates the known_tables variable to include the parent table entity if
        it does not exist already in known_tables.  Looks up the table in the
        atlas_entities if it does not exist.
        :param str parent_table_name:
            The parent table name (not qualified name)
        :param dict(str, dict): All tables we've seen so far.
        :param atlas_entities:
            A list of :class:`~pyapacheatlas.core.entity.AtlasEntity`
            containing the referred entities.
        :type atlas_entities:
            list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
        :return: None
        :rtype: NoneType
        """
        if parent_table_name not in known_tables:
            parent_entity = reader_util.first_entity_matching_attribute(
                "name", parent_table_name, atlas_entities)
            known_tables[parent_table_name] = parent_entity

    def _find_column_type(self, parentTypeName, atlas_typedefs):
        """
        For the given type, find a relationship def that includes "columns" in
        the end def1 (presumably the table end of the relationship) and then
        extract the type from the end def2 (presumably the column end of the)
        relationship.

        :param str parentTypeName: The name of the table type.
        :param dict(str, dict) atlas_typedefs:
            The results of requesting all type defs from Apache Atlas,
            including entityDefs, relationshipDefs, etc.  relationshipDefs
            are the only values used.
        """
        columns_relationship = reader_util.first_relationship_that_matches(
            end_def="endDef1",
            end_def_type=parentTypeName,
            end_def_name="columns",
            relationship_typedefs=atlas_typedefs["relationshipDefs"]
        )
        column_type = columns_relationship["endDef2"]["type"]
        return column_type

    def _insert_column_entity(self, prefix, row, column_type, headers, column_entities, parent_table_entity):
        """

        :param str prefix: The prefix used to filter down the attributes.
        :param dict(str, str) row:
            Represents a row containing the attributes to convert into an atlas
            entity.
        :param str column_type: The column type to be used for this entity.
        :param dict(str, str) headers:
            The headers to aide in looking up field values.
        :param column_entities:
            The column entities dictionary that will be inserted into.
        :type column_entities:
            list(`:class:~pyapacheatlas.core.entity.AtlasEntity`)
        :param parent_table_entity: The parent table entity for this column.
        :type parent_table_entity:
            `:class:~pyapacheatlas.core.entity.AtlasEntity`
        """
        _qual_name = reader_util._make_col_qual_name(
            row[headers["column"]], parent_table_entity.name)

        _clean_attribs = reader_util.columns_matching_pattern(
            row, prefix,
            does_not_match=list(headers.values())
        )
        _attributes = self._organize_attributes(
            _clean_attribs,
            column_entities,
            []
        )
        _attributes["relationshipAttributes"].update(
            {
                "table": parent_table_entity.to_json(
                    minimum=True)
            }
        )
        _classifications = reader_util.string_to_classification(
            row.get(headers["classifications"])
        )

        # There should always be a target
        new_entity = AtlasEntity(
            name=row[headers["column"]],
            typeName=column_type,
            # qualifiedName can be overwritten via the attributes
            # functionality
            qualified_name=_qual_name,
            guid=self.guidTracker.get_guid(),
            attributes=_attributes["attributes"],
            # TODO: Make the relationship name dynamic instead of only table
            relationshipAttributes=_attributes["relationshipAttributes"],
            classifications=_classifications
        )
        if new_entity in column_entities:
            popped_entity = column_entities.pop(new_entity)
            new_entity.merge(popped_entity)
        # Add to outputs
        payload = {new_entity.qualifiedName: new_entity}
        column_entities.update(payload)

        return _qual_name

    def parse_finegrain_column_lineage(self, json_rows, atlas_entities, atlas_typedefs, use_column_mapping=False):
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
        _required_headers = ["table", "column", "classifications"]
        source_header = {k: "{} {}".format(
            self.config.source_prefix, k) for k in _required_headers}
        target_header = {k: "{} {}".format(
            self.config.target_prefix, k) for k in _required_headers}

        transformation_column_header = self.config.column_transformation_name
        # No required process headers

        columnEntitiesOutput = OrderedDict()
        # `tables` Stores all of the table entities by their name seen in the
        # loop for faster lookup
        tables = {}
        # dataset_mapping:
        # {"input_table":"","output_table":"","columnMapping":[]}
        dataset_mapping = {}
        # Caches all of the table processes seen in the loop for faster lookup
        table_and_proc_mappings = {}

        for row in json_rows:
            # Set up defaults
            target_qual_name, source_qual_name, process_qual_name = None, None, None
            table_process = None
            # Given the existing table entity in atlas_entities,
            # look up the appropriate column type

            self._update_parent_table_cache(
                row[target_header["table"]], tables, atlas_entities)

            target_parent = tables[row[target_header["table"]]]
            target_column_type = self._find_column_type(
                target_parent.typeName, atlas_typedefs)

            target_qual_name = self._insert_column_entity(
                self.config.target_prefix, row, target_column_type,
                target_header,
                columnEntitiesOutput, target_parent
            )

            # Source Column is optiona in the spreadsheet
            if row[source_header["table"]] is not None:
                # Given the existing source table entity in atlas_entities,
                # look up the appropriate column type
                self._update_parent_table_cache(
                    row[source_header["table"]], tables, atlas_entities)

                source_parent = tables[row[source_header["table"]]]
                source_column_type = self._find_column_type(
                    source_parent.typeName, atlas_typedefs)

                source_qual_name = self._insert_column_entity(
                    self.config.source_prefix, row, source_column_type,
                    source_header,
                    columnEntitiesOutput, source_parent
                )
                table_process = reader_util.first_process_containing_io(
                    row[source_header["table"]], row[target_header["table"]],
                    atlas_entities)

            # Given the existing process that with target table and source
            # table types, look up the appropriate column_lineage type
            # LIMITATION: Prevents you from specifying multiple processes
            # for the same input and output tables
            if row[source_header["table"]] is None:
                table_process = reader_util.first_process_containing_io(
                    "*", row[target_header["table"]], atlas_entities)

            if table_process.name in table_and_proc_mappings:
                process_type = table_and_proc_mappings[table_process.name]["column_lineage_type"]
            else:
                process_type = reader_util.from_process_lookup_col_lineage(
                    table_process.name,
                    atlas_entities,
                    atlas_typedefs["relationshipDefs"]
                )
                table_and_proc_mappings[table_process.name] = {
                    "column_lineage_type": process_type
                }

            # Assuming there is always a Process for adding at least the
            # target table
            process_attributes = reader_util.columns_matching_pattern(
                row, self.config.process_prefix)
            process_attributes.update({"dependencyType": "SIMPLE"})
            if row[transformation_column_header] is not None:
                process_attributes.update(
                    {"dependencyType": "EXPRESSION",
                     "expression": row[transformation_column_header]
                     })

            process_qual_name = (
                table_process.name +
                "@derived_column:{}".format(
                    row[target_header["column"]]
                ))

            _proc_inputs = [] if source_qual_name not in columnEntitiesOutput else [
                columnEntitiesOutput[source_qual_name].to_json(minimum=True)]
            _proc_output = [
                columnEntitiesOutput[target_qual_name].to_json(minimum=True)]

            process_entity = AtlasProcess(
                name=table_process.name,
                typeName=process_type,
                # qualifiedName can be overwritten via the
                # attributes functionality
                qualified_name=process_qual_name,
                guid=self.guidTracker.get_guid(),
                # Assuming always a single output
                inputs=_proc_inputs,
                outputs=_proc_output,
                attributes=process_attributes,
                # TODO: Make the relationship name more dynamic instead of
                # hard coding query
                relationshipAttributes={
                    "query": table_process.to_json(minimum=True)}
            )
            if process_entity in columnEntitiesOutput:
                popped_entity = columnEntitiesOutput.pop(process_entity)
                process_entity.merge(popped_entity)
            # Add to outputs
            columnEntitiesOutput.update(
                {process_entity.qualifiedName: process_entity})

            if use_column_mapping:
                # Handles multiple source columns from multiple source datasets
                col_map_source_col = (
                    "*" if source_qual_name is None
                    else columnEntitiesOutput[source_qual_name].name
                )
                col_map_target_col = (
                    columnEntitiesOutput[target_qual_name].name
                )
                col_map_source_table = row[source_header["table"]] or "*"
                col_map_target_table = row[target_header["table"]]
                hash_key = hash(col_map_source_table + col_map_target_table)
                col_map_dict = {"Source": col_map_source_col,
                                "Sink": col_map_target_col}
                data_map_dict = {"Source": col_map_source_table,
                                 "Sink": col_map_target_table}

                if table_process.guid in dataset_mapping:
                    if hash_key in dataset_mapping[table_process.guid]:
                        # Hash Key has not been seen before
                        (
                            dataset_mapping[table_process.guid][hash_key]["ColumnMapping"]
                            .append(col_map_dict)
                        )
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
        output = [e for e in list(columnEntitiesOutput.values())]
        return output

    def _determine_dataset_to_use(self, qual_name, typeName):
        results = []
        if qual_name is None:
            # This will allow us to do a partial update.
            results = None
        elif qual_name == "N/A":
            # N/A is a special keyword that forces us to override
            # and delete the existing input/output
            results = []
        else:
            # This is an AtlasObjectId, necessary if we don't have the
            # guid of the existing object or have it as a referenced object
            results = [{"typeName": typeName,
                        "uniqueAttributes": {"qualifiedName": qual_name}}]
        return results

    def _header_qn(self, l):
        return l["uniqueAttributes"]["qualifiedName"]

    def parse_update_lineage(self, json_rows):
        """
        Take in UpdateLineage dictionaries and create the mutated Process
        entities to be uploaded. All referenced entities must already exist
        and be identified by their type and qualifiedName.

        Assumes a None entry for target or source qualifiedNames means 
        "no change" to the existing entity. Using 'N/A' for the target or
        source qualifiedNames will reset the existing input or output to an
        empty list.

        :param json_rows:
            A list of dicts that contain the converted rows of your update
            lineage spreadsheet.
        :type json_rows: list(dict(str,str))
        :return:
            A list of Atlas Processes as dictionaries representing the updated
            process entity.
        :rtype: list(dict)
        """
        results = []
        sp = self.config.source_prefix
        tp = self.config.target_prefix
        pp = self.config.process_prefix

        processes_seen = dict()

        for row in json_rows:
            try:
                target_type = row[f"{tp} typeName"]
                target_qual_name = row[f"{tp} qualifiedName"]
                source_type = row[f"{sp} typeName"]
                source_qual_name = row[f"{sp} qualifiedName"]
                process_type = row[f"{pp} typeName"]
                process_qual_name = row[f"{pp} qualifiedName"]
                process_name = row[f"{pp} name"]
            except KeyError:
                raise Exception(json.dumps(row))

            # Determine whether this should destroy one side, partial update
            # (one side), or full update (both sides).
            inputs = self._determine_dataset_to_use(
                source_qual_name, source_type)
            outputs = self._determine_dataset_to_use(
                target_qual_name, target_type)

            if process_qual_name in processes_seen:
                temp_proc = processes_seen[process_qual_name]
                # Get the inputs and outputs as they exist before this row
                temp_in = temp_proc.inputs
                temp_out = temp_proc.outputs
                # If we have an input, check if it already exists
                if inputs and len(inputs) > 0:
                    input_qn = self._header_qn(inputs[0])
                    if input_qn not in [self._header_qn(x) for x in temp_in]:
                        temp_in.extend(inputs)
                        temp_proc.inputs = temp_in

                    else:
                        warnings.warn(
                            f"Input '{input_qn}' is repeated in Process '{process_qual_name}'. Only the earliest entry is kept.")
                elif isinstance(inputs, list):
                    # We have an empty list, as the input, meaning destroy the input
                    if len(temp_in) > 0:
                        warnings.warn(
                            f"Process '{process_qual_name}' has conflicting inputs and N/A values and will possibly be overwritten.")
                    temp_proc.inputs(inputs)

                if outputs:
                    output_qn = self._header_qn(outputs[0])
                    if output_qn not in [self._header_qn(x) for x in temp_out]:
                        temp_out.extend(outputs)
                        temp_proc.outputs = temp_out
                    else:
                        warnings.warn(
                            f"Output '{output_qn}' is repeated in Process '{process_qual_name}'. Only the earliest entry is kept.")
                elif isinstance(outputs, list):
                    # We have an empty list, as the output, meaning destroy the output
                    if len(temp_out) > 0:
                        warnings.warn(
                            f"Process '{process_qual_name}' has conflicting outputs and N/A values and will possibly be overwritten.")
                    temp_proc.outputs = outputs

            else:
                proc = AtlasProcess(
                    name=process_name,
                    typeName=process_type,
                    qualified_name=process_qual_name,
                    guid=self.guidTracker.get_guid(),
                    inputs=inputs,
                    outputs=outputs
                )
                processes_seen[process_qual_name] = proc

            results = [v.to_json() for v in processes_seen.values()]
        return results

    def parse_column_mapping(self, json_rows):
        """
        Take in ColumnMapping dictionaries and create the mutated Process
        entities to be uploaded. All referenced entities should already exist
        and be identified by their type and qualifiedName.

        Creates process entities with only the columnMapping field filled in.

        :param json_rows:
            A list of dicts that contain the converted rows of your update
            lineage spreadsheet.
        :type json_rows: list(dict(str,str))
        :return: An AtlasTypeDef with entityDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        results = []
        sp = self.config.source_prefix
        tp = self.config.target_prefix
        pp = self.config.process_prefix

        processes_seen = dict()
        # {proc: {in-data|out-data:[{'Source':,'Sink':}]}}

        for row in json_rows:
            try:
                target_col = row[f"{tp} column"]
                target_qual_name = row[f"{tp} qualifiedName"]
                source_col = row[f"{sp} column"]
                source_qual_name = row[f"{sp} qualifiedName"]
                process_name = row[f"{pp} name"]
                process_type = row[f"{pp} typeName"]
                process_qual_name = row[f"{pp} qualifiedName"]
            except KeyError:
                raise Exception(
                    "This row does not contain all of the required fields (" +
                    ', '.join([f"{tp} column", f"{tp} qualifiedName", f"{sp} column", f"{sp} column", f"{pp} name", f"{tp} typeName", f"{pp} qualifiedName"]) + '): ' +
                    json.dumps(row)
                )

            dataset_key = f"{source_qual_name}|{target_qual_name}"
            column_mapping = {"Source": source_col, "Sink": target_col}
            if process_qual_name in processes_seen:
                # Updating the entity
                working_process = processes_seen[process_qual_name]
                if dataset_key in working_process["mappings"]:
                    working_process["mappings"][dataset_key].append(
                        column_mapping)
                else:
                    working_process["mappings"][dataset_key] = [column_mapping]
            else:
                # Creating a new one
                processes_seen[process_qual_name] = {
                    "mappings": {dataset_key: [column_mapping]},
                    "processType": process_type,
                    "processName": process_name
                }

        for proc_qn, proc in processes_seen.items():
            columnMapping = []
            for dataset in proc["mappings"]:
                # Split apart the pipe delimited data
                src_data, sink_data = dataset.split("|", 1)
                # Create the column mapping data structure
                columnMapping.append(
                    {
                        "DatasetMapping": {"Source": src_data, "Sink": sink_data},
                        "ColumnMapping": proc["mappings"][dataset]
                    }
                )

            proc_entity = AtlasProcess(
                name=proc["processName"],
                typeName=proc["processType"],
                qualified_name=proc_qn,
                guid=self.guidTracker.get_guid(),
                inputs=None,
                outputs=None,
                attributes={"columnMapping": json.dumps(columnMapping)}
            )
            results.append(proc_entity.to_json())

        return results
