import requests
import config
from entity_handler import EntityHandler
import logging

eh = EntityHandler()


def get_all_projects():
    r = requests.get(
        "http://dev-services.agilestructure.in/api/v1/projects.json",
        headers={"Authorization": config.WRS_ACCESS_TOKENS},
        params={})
    r = r.json()
    if "error" in r:
        logging.info("Error In Projects fetching from WRS ::: {}".format(r[
            "error"]))
    return r


def fetch_all_project_names():
    return set([
        project[config.WRS_PROJECT_NAME] for project in get_all_projects()
        if config.WRS_PROJECT_NAME in project
    ])


def update_entity_names(entity_name="projectName"):
    project_names = {
        pname.lower(): pname
        for pname in fetch_all_project_names()
    }
    if not project_names:
        return
    entities = eh.fetch_all_entities(
        project_id=config.PROJECT_ID,
        entity_type_id=config.ENTITIES[entity_name])
    synonym_entity_map = {}
    for ename, synonyms in entities.items():
        synonym_entity_map[ename.lower()] = ename
        for synonym in synonyms:
            synonym_entity_map[synonym.lower()] = ename
    '''Remove Non Used Projects'''
    removable_entities = set(entities.keys()).difference([
        synonym_entity_map[synonym]
        for synonym in set(synonym_entity_map.keys()).intersection(
            project_names.keys())
    ])
    for pname in removable_entities:
        eh.delete_entity(
            project_id=config.PROJECT_ID,
            entity_type_id=config.ENTITIES[entity_name],
            entity_value=pname)
    '''Add Newly Added Projects'''
    newly_added_projects = [
        project_names[pname]
        for pname in set(project_names.keys()).difference(
            synonym_entity_map.keys())
    ]
    for pname in newly_added_projects:
        eh.add_new_entity(
            project_id=config.PROJECT_ID,
            entity_type_id=config.ENTITIES[entity_name],
            entity_value=pname)
    '''Add Project Synonyms'''
    for pname in set(project_names.keys()).intersection(
            synonym_entity_map.keys()):
        if project_names[pname] != synonym_entity_map[pname] and project_names[
                pname] not in set(entities[synonym_entity_map[pname]]):
            eh.add_new_entity(
                project_id=config.PROJECT_ID,
                entity_type_id=config.ENTITIES[entity_name],
                entity_value=synonym_entity_map[pname],
                synonyms=list(entities[synonym_entity_map[pname]]) +
                [project_names[pname]])


if __name__ == "__main__":
    update_entity_names()
