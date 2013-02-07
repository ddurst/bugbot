#!/usr/bin/python

import urllib2
import re
import datetime
import subprocess
import os
import json

CONFIG_JSON = os.getcwd() + "/scripts/configs/config.json"
config = json.load(open(CONFIG_JSON, 'r'))
scripts_dir =  os.getcwd() + "/scripts/"
queries_dir =  os.getcwd() + "/queries/"

def getTemplateValue(url):
	version_regex = re.compile(".*<p>(.*)</p>.*")
	template_page = urllib2.urlopen(url).read().replace('\n', '')
	parsed_template = version_regex.match(template_page)
	return parsed_template.groups()[0]

def getReportURL(approval_flag, span):
	a = urllib2.urlopen("https://bugzilla.mozilla.org/page.cgi?id=release_tracking_report.html&q=" + approval_flag + "%3A%2B%3A" + span + "%3A0%3Aand%3A")
	return a.url

def createQuery(title, short_title, url, show_summary):
	file_name = queries_dir + str(datetime.date.today()) + '_' + short_title

	qf = open(file_name, 'w')
	qf.write("query_name = \'" + title + "\'\n")
    print "Query Title: %s" % title
	qf.write("query_url = \'" + url + "\'\n")
    print "Query Url: %s" % url
	qf.write("show_summary = \'" + str(show_summary) + "\'\n")

	return file_name 

def createQueriesList():

    beta_version =		getTemplateValue("https://wiki.mozilla.org/Template:BETA_VERSION")
    aurora_version =	getTemplateValue("https://wiki.mozilla.org/Template:AURORA_VERSION")
    central_version =	getTemplateValue("https://wiki.mozilla.org/Template:CENTRAL_VERSION")
    esr_version =		getTemplateValue("https://wiki.mozilla.org/Template:ESR_VERSION")
    cycle_span =		getTemplateValue("https://wiki.mozilla.org/Template:CURRENT_CYCLE")

    unlanded_beta_url =	getReportURL("approval-mozilla-beta", 	cycle_span) + ";field0-0-0=cf_status_firefox" + beta_version + ";type0-0-0=nowordssubstr;value0-0-0=unaffected%2C fixed%2C verified%2C wontfix"
    unlanded_aurora_url =	getReportURL("approval-mozilla-aurora", cycle_span) + ";field0-0-0=cf_status_firefox" + aurora_version + ";type0-0-0=nowordssubstr;value0-0-0=unaffected%2C fixed%2C verified%2C wontfix"
    unlanded_esr17_url =	getReportURL("approval-mozilla-esr17",	cycle_span) + ";field0-0-0=cf_status_firefox_esr" + esr_version + ";type0-0-0=nowordssubstr;value0-0-0=unaffected%2C fixed%2C verified%2C wontfix"

    tracking_beta_url = "https://bugzilla.mozilla.org/buglist.cgi?type1-0-0=equals;type0-1-0=notequals;type0-5-0=notequals;value0-5-0=disabled;value0-4-0=verified;field0-1-0=cf_status_firefox" + beta_version + ";field0-0-0=cf_tracking_firefox" + beta_version + ";field2-0-0=flagtypes.name;value0-3-0=unaffected;value0-6-0=verified%20disabled;value0-1-0=wontfix;field0-5-0=cf_status_firefox" + beta_version + ";type0-0-0=equals;value0-0-0=%2B;type0-2-0=notequals;negate1=1;field0-3-0=cf_status_firefox" + beta_version + ";type0-4-0=notequals;columnlist=bug_severity%2Cpriority%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox17%2Ccf_tracking_firefox" + beta_version + "%2Ccf_status_firefox17%2Ccf_status_firefox" + beta_version + ";value2-0-0=approval-mozilla-beta%3F;field0-6-0=cf_status_firefox" + beta_version + ";type2-0-0=notsubstring;query_format=advanced;value0-2-0=fixed;type0-3-0=notequals;value1-0-0=core-security;field0-2-0=cf_status_firefox" + beta_version + ";field0-4-0=cf_status_firefox" + beta_version + ";type0-6-0=notequals;field1-0-0=bug_group"

    tracking_aurora_url = "https://bugzilla.mozilla.org/buglist.cgi?type1-0-0=equals;type0-1-0=notequals;type0-5-0=notequals;value0-5-0=disabled;value0-4-0=verified;type3-0-0=notequals;field0-1-0=cf_status_firefox" + aurora_version + ";field0-0-0=cf_tracking_firefox" + aurora_version + ";field2-0-0=flagtypes.name;value0-3-0=unaffected;value0-6-0=verified%20disabled;value0-1-0=wontfix;field0-5-0=cf_status_firefox" + aurora_version + ";type0-0-0=equals;value0-0-0=%2B;type0-2-0=notequals;negate1=1;field0-3-0=cf_status_firefox" + aurora_version + ";type0-4-0=notequals;value3-0-0=%2B;columnlist=bug_severity%2Cpriority%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox17%2Ccf_tracking_firefox" + beta_version  + "%2Ccf_status_firefox17%2Ccf_status_firefox" + beta_version  + ";value2-0-0=approval-mozilla-aurora%3F;field0-6-0=cf_status_firefox" + aurora_version + ";field3-0-0=cf_tracking_firefox" + beta_version  + ";type2-0-0=notsubstring;query_format=advanced;value0-2-0=fixed;type0-3-0=notequals;value1-0-0=core-security;field0-2-0=cf_status_firefox" + aurora_version + ";field0-4-0=cf_status_firefox" + aurora_version + ";type0-6-0=notequals;field1-0-0=bug_group"

    tracking_central_url = "https://bugzilla.mozilla.org/buglist.cgi?negate1=1;field0-3-0=cf_status_firefox" + central_version + ";value3-1-0=%2B;type1-0-0=equals;type0-1-0=notequals;type0-5-0=notequals;value0-5-0=disabled;value0-4-0=verified;list_id=5128263;type3-0-0=notequals;field0-1-0=cf_status_firefox" + central_version + ";field0-0-0=cf_tracking_firefox" + central_version + ";type0-4-0=notequals;value3-0-0=%2B;columnlist=bug_severity%2Cpriority%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox17%2Ccf_tracking_firefox" + beta_version + "%2Ccf_status_firefox17%2Ccf_status_firefox" + beta_version + ";value2-0-0=approval-mozilla-aurora%3F;field2-0-0=flagtypes.name;field3-1-0=cf_tracking_firefox" + aurora_version + ";field0-6-0=cf_status_firefox" + central_version + ";value0-3-0=unaffected;field3-0-0=cf_tracking_firefox" + beta_version + ";type2-0-0=notsubstring;query_format=advanced;value0-2-0=fixed;value0-6-0=verified%" + central_version + "disabled;value0-1-0=wontfix;type0-3-0=notequals;value1-0-0=core-security;field0-2-0=cf_status_firefox" + central_version + ";type3-1-0=notequals;field0-5-0=cf_status_firefox" + central_version + ";field0-4-0=cf_status_firefox" + central_version + ";type0-6-0=notequals;type0-0-0=equals;value0-0-0=%2B;type0-2-0=notequals;field1-0-0=bug_group"

    tracking_beta_touch_url = "https://bugzilla.mozilla.org/buglist.cgi?negate1=1;field0-3-0=cf_status_firefox" + beta_version + ";value3-1-0=[no-nag];type1-0-0=equals;type0-1-0=notequals;type0-5-0=notequals;value0-5-0=disabled;value0-4-0=verified;type3-0-0=greaterthan;field0-1-0=cf_status_firefox" + beta_version + ";field0-0-0=cf_tracking_firefox" + beta_version + ";type0-4-0=notequals;value3-0-0=3;columnlist=bug_severity%2Cpriority%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox17%2Ccf_tracking_firefox" + beta_version + "%2Ccf_status_firefox17%2Ccf_status_firefox" + beta_version + ";value2-0-0=approval-mozilla-beta%3F;field2-0-0=flagtypes.name;field3-1-0=status_whiteboard;field0-6-0=cf_status_firefox" + beta_version + ";value0-3-0=unaffected;field3-0-0=owner_idle_time;type2-0-0=notsubstring;query_format=advanced;value0-2-0=fixed;value0-6-0=verified%20disabled;value0-1-0=wontfix;type0-3-0=notequals;value1-0-0=core-security;field0-2-0=cf_status_firefox" + beta_version + ";type3-1-0=notsubstring;field0-5-0=cf_status_firefox" + beta_version + ";field0-4-0=cf_status_firefox" + beta_version + ";type0-6-0=notequals;type0-0-0=equals;value0-0-0=%2B;type0-2-0=notequals;field1-0-0=bug_group"

    tracking_aurora_touch_url = "https://bugzilla.mozilla.org/buglist.cgi?negate1=1;field0-3-0=cf_status_firefox" + aurora_version + ";type4-0-0=greaterthan;type1-0-0=equals;type0-1-0=notequals;type0-5-0=notequals;value0-5-0=disabled;value0-4-0=verified;type3-0-0=notequals;field0-1-0=cf_status_firefox" + aurora_version + ";field0-0-0=cf_tracking_firefox" + aurora_version + ";type0-4-0=notequals;value3-0-0=%2B;field4-0-0=owner_idle_time;columnlist=bug_severity%2Cpriority%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox17%2Ccf_tracking_firefox" + beta_version + "%2Ccf_status_firefox17%2Ccf_status_firefox" + beta_version + ";value2-0-0=approval-mozilla-aurora%3F;field2-0-0=flagtypes.name;field0-6-0=cf_status_firefox" + aurora_version + ";value0-3-0=unaffected;field3-0-0=cf_tracking_firefox" + beta_version + ";type2-0-0=notsubstring;query_format=advanced;value0-2-0=fixed;value0-6-0=verified%20disabled;value0-1-0=wontfix;type0-3-0=notequals;value1-0-0=core-security;field0-2-0=cf_status_firefox" + aurora_version + ";field0-5-0=cf_status_firefox" + aurora_version + ";value4-0-0=3;field0-4-0=cf_status_firefox" + aurora_version + ";type0-6-0=notequals;type0-0-0=equals;value0-0-0=%2B;type0-2-0=notequals;field1-0-0=bug_group"

    tracking_central_touch_url = "https://bugzilla.mozilla.org/buglist.cgi?negate1=1;field0-3-0=cf_status_firefox" + central_version + ";type1-0-0=equals;type2-1-0=notequals;type0-1-0=notequals;type0-5-0=notequals;value0-5-0=disabled;value0-4-0=verified;list_id=5128283;type3-0-0=greaterthan;field0-1-0=cf_status_firefox" + central_version + ";field0-0-0=cf_tracking_firefox" + central_version + ";type0-4-0=notequals;value3-0-0=3;columnlist=bug_severity%2Cpriority%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox17%2Ccf_tracking_firefox" + beta_version + "%2Ccf_status_firefox17%2Ccf_status_firefox" + beta_version + ";value2-0-0=%2B;field2-0-0=cf_tracking_firefox" + beta_version + ";field0-6-0=cf_status_firefox" + central_version + ";value0-3-0=unaffected;field3-0-0=owner_idle_time;type2-0-0=notequals;query_format=advanced;value0-2-0=fixed;value0-6-0=verified%" + central_version + "disabled;value0-1-0=wontfix;type0-3-0=notequals;value2-1-0=%2B;value1-0-0=core-security;field0-2-0=cf_status_firefox" + central_version + ";field0-5-0=cf_status_firefox" + central_version + ";field0-4-0=cf_status_firefox" + central_version + ";type0-6-0=notequals;type0-0-0=equals;value0-0-0=%2B;field2-1-0=cf_tracking_firefox" + aurora_version + ";type0-2-0=notequals;field1-0-0=bug_group"

    tracking_esr10_url = "https://bugzilla.mozilla.org/buglist.cgi?type0-1-0=nowordssubstr;field0-1-0=cf_status_esr10;field0-0-0=cf_tracking_esr10;query_format=advanced;value0-1-0=fixed%20verified%20disabled%20wontfix%20unaffected;type0-0-0=equals;value0-0-0=" + beta_version + "%2B"

    tracking_esr17_url =  "https://bugzilla.mozilla.org/buglist.cgi?type0-1-0=nowordssubstr;field0-1-0=cf_status_esr17;field0-0-0=cf_tracking_esr17;query_format=advanced;value0-1-0=fixed%20verified%20disabled%20wontfix%20unaffected;type0-0-0=equals;value0-0-0=" + beta_version + "%2B"

    queries = []
    weekday = datetime.datetime.today().weekday()

    if weekday >= 0 and weekday < 5:
    	queries.append(createQuery("Unlanded Beta " + beta_version + " Bugs", "unlanded_beta", unlanded_beta_url, 1))
    	queries.append(createQuery("Unlanded Aurora " + aurora_version + " Bugs", "unlanded_aurora", unlanded_aurora_url, 1))
    	queries.append(createQuery("Unlanded ESR17 Bugs", "unlanded_esr17", unlanded_esr17_url, 0))

    if weekday == 0:
    	queries.append(createQuery("Bugs Tracked for Beta " + beta_version, "tracking_beta", tracking_beta_url, 1))
    	queries.append(createQuery("Bugs Tracked for Aurora " + aurora_version, "tracking_aurora", tracking_aurora_url, 1))
    	queries.append(createQuery("Bugs Tracked for Nightly " + central_version, "tracking_central", tracking_central_url, 1))
    	queries.append(createQuery("Bugs Tracked for ESR10", "tracking_esr10", tracking_esr10_url, 0))
    	queries.append(createQuery("Bugs Tracked for ESR17", "tracking_esr17", tracking_esr17_url, 0))

    if weekday == 4:
    	queries.append(createQuery("Tracked Beta " + beta_version + " Bugs, untouched this week", "untouched_tracking_beta", tracking_beta_touch_url, 1))
    	queries.append(createQuery("Tracked Aurora " + aurora_version + " Bugs, untouched this week", "untouched_tracking_aurora", tracking_aurora_touch_url, 1))
    	queries.append(createQuery("Tracked Nightly " + central_version + " Bugs, untouched this week", "untouched_tracking_nightly", tracking_central_touch_url, 1))
    
    # TODO - sort the queries according to a priority flag
    return queries

def cleanUp():
    for file in os.listdir(queries_dir):
        if file.startswith(str(datetime.date.today())):
            os.remove(os.path.join(queries_dir,file))

if __name__ == '__main__':
    queries = createQueriesList()
    command = [scripts_dir + "email_nag.py", "-t", "daily_email", "--no-verification", "-m", config['ldap_username'], "-p", config['ldap_password']]
    # USE FOR DEBUGGING
    #command.append('-d')
    for query in queries:
    	command.append('-q')
        command.append(query)
    subject = datetime.datetime.today().strftime("%A %b %d") + " -- Daily Release Tracking Alert"
    command.extend(['-s',  subject])
    subprocess.call(command)
    cleanUp()

