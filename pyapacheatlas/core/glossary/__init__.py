class AtlasGlossaryTerm():
    
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
        self.name = kwargs.get("name")
        self.nickName = kwargs.get("nickName") or kwargs.get("name")
        self.parentTerm = kwargs.get("parentTerm")
        
        self.abbreviation = kwargs.get("abbreviation")
        self.additionalAttributes = kwargs.get("additionalAttributes")
        self.anchor = {"glossaryGuid": kwargs.get("glossaryGuid")} if kwargs.get("glossaryGuid") else kwargs.get("anchor")
        self.attributes = kwargs.get("attributes", {})
        # Purview Only
        self.contacts = kwargs.get("contacts")
        self.guid = kwargs.get("guid")
        self.examples = kwargs.get("examples") #list(str)
        self.longDescription = kwargs.get("long_description")
        self.qualifiedName = kwargs.get("qualifiedName")
        self.resources = kwargs.get("resources")
        # Atlas Only
        self.shortDescription = kwargs.get("shortDescription")
        # Draft, Active, Alert, Expired
        self.status = kwargs.get("status", "Draft")
        self.usage = kwargs.get("usage")
        
        # These are all supposed to be AtlasRelatedTermHeaders
        self.antonyms = kwargs.get("antonyms")
        self.classifies = kwargs.get("classifies")
        self.isA = kwargs.get("isA")
        self.preferredTerms = kwargs.get("preferredTerms")
        self.preferredToTerms = kwargs.get("preferredToTerms")
        self.replacedBy = kwargs.get("replacedBy")
        self.replacementTerms = kwargs.get("replacementTerms")
        self.seeAlso = kwargs.get("seeAlso")
        self.synonyms = kwargs.get("synonyms")
        self.translatedTerms = kwargs.get("translatedTerms")
        self.translationTerms = kwargs.get("translationTerms")
        self.validValues = kwargs.get("validValues")
        self.validValuesFor = kwargs.get("validValuesFor")
    
    def update_hierarchy(self, parentTerm, parentGuid):
        self.parentTerm = {"termGuid": parentGuid}
        self.name = self.parentTerm + "_" + self.nickName
    
    def add_expert(self, objectId, info):
        expert_obj = {"id": objectId, "info": info}
        if self.contacts:
            if "Expert" in self.contacts:
                self.contacts["Expert"].append(expert_obj)
            else:
                self.contacts["Expert"] = [expert_obj]
    
    def add_steward(self, objectId, info):
        steward_obj = {"id": objectId, "info": info}
        if self.contacts:
            if "Steward" in self.contacts:
                self.contacts["Steward"].append(steward_obj)
            else:
                self.contacts["Steward"] = [steward_obj]
