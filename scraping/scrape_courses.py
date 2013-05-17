import re
import requests
import simplejson
from scrapy.selector import HtmlXPathSelector

year_pages = {
    '2006-2007': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1069",
    '2007-2008': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1079",
    '2008-2009': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1089",
    '2009-2010': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1099",
    '2010-2011': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1109",
    '2011-2012': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1119",
    '2012-2013': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?term=1129",
    '2013-2014': "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html"
}

def get_courses_offered_urls_from_year_page(url):
    c = requests.get(url).content
    selector = HtmlXPathSelector(text = c)
    urls = selector.select("//tr/td[@valign='top']/a/@href").extract()
    filtered_urls = filter(lambda url: 'subj_page' in url, urls)
    courses_offered_urls = []
    for url in filtered_urls:
        (subject, term) = re.findall(r"subj_page=([^&]*)&term=(.*)", url)[0]
        courses_offered_url = "https://iasext.wesleyan.edu/regprod/!wesmaps_page.html?crse_list=%s&term=%s&offered=Y" % (subject, term)
        courses_offered_urls.append(courses_offered_url)
    return courses_offered_urls

def get_course_urls_from_courses_offered_page(url):
    c = requests.get(url).content
    selector = HtmlXPathSelector(text = c)
    try:
        course_links = selector.select("//tr/td[@width='5%']/a/@href").extract()
    except:
        course_links = []
    return map(lambda l: "https://iasext.wesleyan.edu/regprod/" + l, course_links)

def get_course_info_from_course_page(url):
    c = requests.get(url).content
    course = {}
    selector = HtmlXPathSelector(text = c)
    course['title'] = selector.select("//span[@class='title']/text()").extract()[0]
    course['department'] = selector.select("//td/b/a/text()").extract()[0]
    course['number'] = selector.select("//td/b/text()").extract()[0].split(' ')[1]
    course['semester'] = selector.select("//td/b/text()").extract()[1].replace('\n', '')

    course['url'] = url
    course['courseid'] = url[60:66]

    try:
        course['credit'] = int( re.findall('Credit: </b>([^<]*)', c)[0] )
    except:
        course['credit'] = 1

    try:
        course['prerequisites'] = re.findall('Prerequisites: </b>([^<]*)', c)[0]
    except:
        course['prerequisites'] = "None"

    try:
        course['genEdArea'] = re.findall('Gen Ed Area Dept: </b>([^<]*)', c)[0].replace('\n','')
    except:
        course['genEdArea'] = "None"

    try:
        course['gradingMode'] = re.findall('Grading Mode: </b>([^<]*)', c)[0].replace('\n','')
    except:
        course['gradingMode'] = "None"

    sectionsSelector = selector.select("//table[@border='1']")
    
    course['sections'] = []

    for sectionSelector in sectionsSelector:
        section = {}

        content = sectionSelector.extract()

        try:
            section['name'] = re.findall('SECTION ([^<]*)', content)[0]
        except:
            section['name'] = "None"

        try:
            section['times'] = re.findall('Times:</b> ([^<]*)', content)[0].replace('\n','').replace('&nbsp;', '')
        except:
            section['times'] = "None"

        try:
            section['location'] = re.findall('Location:</b> ([^<]*)', content)[0].replace('\n','')
        except:
            section['location'] = "None"

        try:
            section['enrollmentLimit'] = int( re.findall('Total Enrollment Limit: </a>([^<]*)', content)[0] )
        except:
            section['enrollmentLimit'] = 0

        try:
            section['GRAD_Major'] = re.findall('GRAD: ([^<]*)', content)[0]
            section['SR_NonMajor'] = re.findall('SR non-major: ([^<]*)', content)[0]
            section['SR_Major'] = re.findall('SR major: ([^<]*)', content)[0]
            section['JR_NonMajor'] = re.findall('JR non-major: ([^<]*)', content)[0]
            section['JR_Major'] = re.findall('JR major: ([^<]*)', content)[0]
            section['SO'] = re.findall('SO: ([^<]*)', content)[0]
            section['FR'] = re.findall('FR: ([^<]*)', content)[0]
            section['permissionRequired'] = False
        except:
            section['permissionRequired'] = True

        course['sections'].append(section)

    return course    


def get_all_courses():
    courses = []
    for year_page_url in year_pages.values():
        courses_offered_urls = get_courses_offered_urls_from_year_page(year_page_url)
        for courses_offered_url in courses_offered_urls:
            course_urls = get_course_urls_from_courses_offered_page(courses_offered_url)
            for course_url in course_urls:
                course = get_course_info_from_course_page(course_url)
                print "Adding", course['title']
                courses.append(get_course_info_from_course_page(course_url))
    return courses            

if __name__ == '__main__':
    courses = get_all_courses()
    open('courses.json').write(simplejson.dumps(courses))