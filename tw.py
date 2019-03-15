# encoding: utf-8

import sys
import argparse
import base64
from workflow import Workflow, ICON_WEB, ICON_WARNING, web, PasswordNotFound

__VERSION__ = '0.1.1'

def get_projects(url, apikey):
    apiurl = url + '/projects.json'
    request_headers = {"Authorization": 'Basic ' + base64.b64encode( apikey + ':xxx' ) }
    request_params = dict(per_page=100, membership=True, archived=False)
    r = web.get(apiurl, params=request_params, headers=request_headers)
    r.raise_for_status()

    results = r.json()
    projects = []
    for result in results['projects']:
        projects.append({
            "name": result['name'],
            "description": result['description'],
            "url": url + '/index.cfm#projects/' + result['id'] + '/tasks'})

    return projects

def search_key(project):
    elements = []
    elements.append(project['name'])
    elements.append(project['description'])

    return u' '.join(elements)

def main(wf):
    parser = argparse.ArgumentParser();
    parser.add_argument( '--setkey', dest='api_key', nargs='?', default=None)
    parser.add_argument( '--seturl', dest='url', nargs='?', default=None)
    parser.add_argument( '--query', dest='query', nargs='?', default=None)

    args = parser.parse_args(wf.args)

    if wf.update_available:
        wf.add_item('New version available',
            'Action this item to install the update',
            autocomplete='workflow:update',
            icon=ICON_INFO)

    if args.url:
        wf.settings['teamwork_url'] = args.url;
        return 0;

    url = wf.settings.get('teamwork_url', None)
    if not url:
        wf.add_item('No URL set', 'Please use teamwork seturl to set your instance url.', valid=False, icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Check for api key
    if args.api_key:
        wf.save_password( 'teamwork_apikey', args.api_key)
        return 0 #success


    try:
        apikey = wf.get_password( 'teamwork_apikey', None)
    except PasswordNotFound:
        wf.add_item('No API key set', 'Please use teamwork setkey to set your API key.', valid=False, icon=ICON_WARNING)
        wf.send_feedback();
        return 0

    def wrapper():
        return get_projects(url, apikey)

    projects = wf.cached_data('projects', wrapper, max_age=600)

    query = args.query
    if query:
        projects = wf.filter(query, projects, key=search_key, min_score=20)

    for project in projects:
        wf.add_item(title=project['name'], subtitle=project['description'], arg=project['url'], valid=True)

    wf.send_feedback()
    return 0

if __name__ == u"__main__":
    wf = Workflow(update_settings={
        'github_slug': 'ninnypants/teamwork-workflow',
        'version': __VERSION__,
        })
    wf.run(main)
