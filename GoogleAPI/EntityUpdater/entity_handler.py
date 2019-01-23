import dialogflow_v2 as dialogflow
import config


class EntityHandler(object):
    def __init__(self):
        self.entity_types_client = dialogflow.EntityTypesClient()

    def create_entity_type(self, project_id, display_name, kind):
        parent = self.entity_types_client.project_agent_path(project_id)
        entity_type = dialogflow.types.EntityType(
            display_name=display_name, kind=kind)
        response = self.entity_types_client.create_entity_type(parent,
                                                               entity_type)
        print('Entity type created: \n{}'.format(response))

    def delete_entity_type(self, project_id, entity_type_id):
        """Delete entity type with the given entity type name."""
        entity_type_path = self.entity_types_client.entity_type_path(
            project_id, entity_type_id)
        self.entity_types_client.delete_entity_type(entity_type_path)
        print('Deleted Entity type: \n{}'.format(entity_type_id))

    def add_new_entity(self,
                       project_id,
                       entity_type_id,
                       entity_value,
                       synonyms=None):
        synonyms = synonyms or [entity_value]
        entity_type_path = self.entity_types_client.entity_type_path(
            project_id, entity_type_id)
        entity = dialogflow.types.EntityType.Entity()
        entity.value = entity_value
        entity.synonyms.extend(synonyms)
        response = self.entity_types_client.batch_create_entities(
            entity_type_path, [entity])
        print('Entity created: {}'.format(response))

    def delete_entity(self, project_id, entity_type_id, entity_value):
        """Delete entity with the given entity type and entity value."""
        entity_type_path = self.entity_types_client.entity_type_path(
            project_id, entity_type_id)
        self.entity_types_client.batch_delete_entities(entity_type_path,
                                                       [entity_value])
        print('Removed Entity: {}'.format(entity_value))

    def fetch_all_entities(self, project_id, entity_type_id):
        name = self.entity_types_client.entity_type_path(project_id,
                                                         entity_type_id)
        response = self.entity_types_client.get_entity_type(name)
        entities = {}
        for entity in response.entities:
            entities[entity.value] = entity.synonyms
        print('Entity Details: {}'.format(entities))
        return entities


if __name__ == "__main__":
    eh = EntityHandler()
    project_id = config.PROJECT_ID
    entity_type_id = config.ENTITIES["projectName"]
    kind = config.ENTITY_TYPE
    '''Create A New Entity Type'''
    display_name = "autoProjects"
    eh.create_entity_type(project_id, display_name, kind)
    '''Add a Sample Value in Entity'''
    entity_value = "Auto Added Field"
    eh.add_new_entity(
        project_id,
        entity_type_id,
        entity_value,
        synonyms=["AAF", "AutoAddedFields"])
    '''Fetch Details about an Entity'''
    eh.fetch_all_entities(project_id, entity_type_id)
