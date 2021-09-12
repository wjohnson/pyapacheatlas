from ..util import AtlasUnInit


class _CrossPlatformTerm():

    def __init__(self, **kwargs):
        self.abbreviation = kwargs.get("abbreviation", AtlasUnInit())
        self.anchor = {"glossaryGuid": kwargs.get("glossaryGuid")} if kwargs.get(
            "glossaryGuid") else kwargs.get("anchor")
        self.examples = kwargs.get("examples", AtlasUnInit())  # list(str)
        self.guid = kwargs.get("guid", AtlasUnInit())
        self.longDescription = kwargs.get("longDescription", AtlasUnInit())
        self.name = kwargs.get("name")
        self.qualifiedName = kwargs.get("qualifiedName")
        if self.name is None or self.qualifiedName is None:
            raise TypeError("name and qualifiedName are required attributes")
        self.resources = kwargs.get("resources", AtlasUnInit())
        self.usage = kwargs.get("usage", AtlasUnInit())

        # These are all supposed to be AtlasRelatedTermHeaders
        self.antonyms = kwargs.get("antonyms", AtlasUnInit())
        self.classifies = kwargs.get("classifies", AtlasUnInit())
        self.isA = kwargs.get("isA", AtlasUnInit())
        self.preferredTerms = kwargs.get("preferredTerms", AtlasUnInit())
        self.preferredToTerms = kwargs.get("preferredToTerms", AtlasUnInit())
        self.replacedBy = kwargs.get("replacedBy", AtlasUnInit())
        self.replacementTerms = kwargs.get("replacementTerms", AtlasUnInit())
        self.seeAlso = kwargs.get("seeAlso", AtlasUnInit())
        self.synonyms = kwargs.get("synonyms", AtlasUnInit())
        self.translatedTerms = kwargs.get("translatedTerms", AtlasUnInit())
        self.translationTerms = kwargs.get("translationTerms", AtlasUnInit())
        self.validValues = kwargs.get("validValues", AtlasUnInit())
        self.validValuesFor = kwargs.get("validValuesFor", AtlasUnInit())

    def to_json(self, minimum=False):
        """
        :return: The json representation of this term.
        :rtype: dict
        """
        output = dict()
        # Add ins for optional top level attributes
        for k, v in vars(self).items():
            is_uninitialized = isinstance(v, AtlasUnInit)
            is_private = k.startswith("_")
            if is_uninitialized or is_private:
                continue
            output[k] = v

        return output

    @classmethod
    def from_json(cls, term_json):
        """
        Convert a JSON (dict)
        :param dict term_json: A dict representing an Atlas or Purview term.

        :return: The appropriate Purview or Atlas term object.
        """
        return cls(**term_json)


class AtlasGlossaryTerm(_CrossPlatformTerm):

    def __init__(self, **kwargs):
        """
        :param str name:
            A term that you want to upload. Also used as the nickname.
        :param str status: Should be one of Draft, Approved, Alert, Expired.
        :param str glossary_guid:
            The guid of the glossary you want to use. It will call AtlasClient.get_glossary
            with the value of glossary_name if no guid is provided.
        :param dict attributes: Any additional attributes you want to provide to the term.
        :param str parent_formal_name:
            The formal name of the parent term which would be used in the
            hierarchy. It will be concatenated with term's value to create
            the formal name of the uploaded term. Must be provided if you
            plan on using the hierarchy feature of Purview.
        :param str parent_term_guid:
            The guid of the parent term which would be used in the hierarchy.
            If you only provide parent_formal_name, get_glossary_term is
            called to get this guid.
        :param str long_description": A description of your term.
        :param str abbreviation: A comma delimited set of abbreviations.
        :param list(dict) resources:
            An array of resource objects with keys displayName and url.
        :param list(dict) seeAlso:
            Each dictionary should have the key termGuid and value of a guid.
        :param list(dict) synonyms:
            Each dictionary should have the key termGuid and value of a guid.
        :param dict(str,list(dict(str,str))) contacts:
            Root keys of both or either Experts or Stewards and the inner dicts
            in the list should have a key of id with an AAD object id as value
            and key of info with a string.
        """
        super().__init__(**kwargs)
        self.additionalAttributes = kwargs.get(
            "additionalAttributes", AtlasUnInit())
        self.classifications = kwargs.get("classifications", AtlasUnInit())
        self.shortDescription = kwargs.get("shortDescription", AtlasUnInit())


class PurviewGlossaryTerm(_CrossPlatformTerm):

    def __init__(self, **kwargs):
        """
        Create a Purview Glossary Term that supports term template attributes
        and hierarchical parents.


        :param str name:
            A term that you want to upload. Also used as the nickname.
        :param str status: Should be one of Draft, Approved, Alert, Expired.
        :param str glossary_guid:
            The guid of the glossary you want to use. You should call AtlasClient.get_glossary
            to extract the glossary guid.
        :param dict attributes: Any additional attributes you want to provide to the term.
        :param str parent_formal_name:
            The formal name of the parent term which would be used in the
            hierarchy. It will be concatenated with term's value to create
            the formal name of the uploaded term. Must be provided if you
            plan on using the hierarchy feature of Purview.
        :param str parent_term_guid:
            The guid of the parent term which would be used in the hierarchy.
            If you only provide parent_formal_name, get_glossary_term is
            called to get this guid.
        :param str long_description": A description of your term.
        :param str abbreviation: A comma delimited set of abbreviations.
        :param list(dict) resources:
            An array of resource objects with keys displayName and url.
        :param list(dict) seeAlso:
            Each dictionary should have the key termGuid and value of a guid.
        :param list(dict) synonyms:
            Each dictionary should have the key termGuid and value of a guid.
        :param dict(str,list(dict(str,str))) contacts:
            Root keys of both or either Experts or Stewards and the inner dicts
            in the list should have a key of id with an AAD object id as value
            and key of info with a string.
        """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = kwargs.get("name")
        self._qualifiedName = kwargs.get("qualifiedName")
        self.attributes = kwargs.get('attributes', AtlasUnInit())
        self.contacts = kwargs.get('contacts', AtlasUnInit())
        self.createTime = kwargs.get('createTime', AtlasUnInit())
        self.createdBy = kwargs.get('createdBy', AtlasUnInit())
        self.lastModifiedTS = kwargs.get('lastModifiedTS', AtlasUnInit())
        self.updateTime = kwargs.get('updateTime', AtlasUnInit())
        self.updatedBy = kwargs.get('updatedBy', AtlasUnInit())
        self.status = kwargs.get('status', AtlasUnInit())
        self.resources = kwargs.get('resources', AtlasUnInit())

    @property
    def name(self):
        if "_parentFormalName" in vars(self):
            return self._parentFormalName + "_" + self._name
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def nickName(self):
        return self._name

    @property
    def qualifiedName(self):
        if "_parentFormalName" in vars(self):
            return self._parentFormalName + "_" + self._qualifiedName
        return self._qualifiedName

    @qualifiedName.setter
    def qualifiedName(self, value):
        self._qualifiedName = value

    @property
    def parentGuid(self):
        if "parentTerm" in vars(self):
            return self.parentTerm["termGuid"]
        else:
            return None

    @property
    def parentFormalName(self):
        if "parentTerm" in vars(self):
            return self._parentFormalName
        else:
            return None

    def add_hierarchy(self, parentFormalName, parentGuid):
        """
        Add hierarchy to your term. It creates the parentTerm property
        and requires the parent's guid and the parent's formal name.

        :param str parentTerm: The formal name of the parent term.
        :param str parentGuid: The guid of the parent term.
        """
        self.parentTerm = {"termGuid": parentGuid}
        self._parentFormalName = parentFormalName

    def add_expert(self, objectId, info=""):
        """
        Add an expert to your term's contacts. You must provide the AAD object
        id and can optionally provide some information about the user.

        :param str objectId: The AAD object Id of the user.
        :param str info: Optional information about the user.
        """
        expert_obj = {"id": objectId, "info": info}
        if self.contacts:
            if "Expert" in self.contacts:
                self.contacts["Expert"].append(expert_obj)
            else:
                self.contacts["Expert"] = [expert_obj]
        else:
            self.contacts = {
                "Expert": [expert_obj],
                "Steward": [],
            }

    def add_steward(self, objectId, info=""):
        """
        Add a steward to your term's contacts. You must provide the AAD object
        id and can optionally provide some information about the user.

        :param str objectId: The AAD object Id of the user.
        :param str info: Optional information about the user.
        """
        steward_obj = {"id": objectId, "info": info}
        if self.contacts:
            if "Steward" in self.contacts:
                self.contacts["Steward"].append(steward_obj)
            else:
                self.contacts["Steward"] = [steward_obj]
        else:
            self.contacts = {
                "Expert": [],
                "Steward": [steward_obj],
            }

    def to_json(self):
        output = super().to_json()

        output["name"] = self.name
        output["qualifiedName"] = self.qualifiedName
        if "parentTerm" in vars(self):
            output["nickName"] = self.nickName

        return output
