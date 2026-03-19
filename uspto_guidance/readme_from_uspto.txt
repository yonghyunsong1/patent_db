
API syntax examples
Was this page helpful?
To query ODP, you can use simplified or advanced query syntax for more simple or advanced use cases, respectively. The simplified syntax is meant for a “quick start” and may be used by more casual users to have more flexibility in searching the same data available on the searchable Patent File Wrapper user interface. It can be used directly in a web browser or any API usage/testing tool such as Postman. As the name indicates, the focus is on its simplicity, and some more sophisticated search features may not be available. The advanced syntax is slightly more advanced and can be used by query tools such as Postman or in a script.

To use either simplified or advanced syntax, you must first register and obtain an API key. But first, let’s look at some examples of both syntaxes.

Simplified Syntax Examples:
Simplified syntax uses simple query string name/value pairs where the name represents a field you want to match, and the value represents the value you are looking for.

PDF icon View the full simplified syntax documentation

Example 1: Search across multiple fields for anything matching the word "Utility”.

https://api.uspto.gov/api/v1/patent/applications/search?q=Utility

Example 2: Search for invention title including the word "Certification" filed between 2021 and 2022.

https://api.uspto.gov/api/v1/patent/applications/search?q=applicationMetaData.inventionTitle:Apple* AND applicationMetaData.filingDate:[2021-01-01 TO 2022-12-01]&offset=0&limit=25

Advanced Syntax Examples:
The advanced syntax uses the JSON format to provide the field name and its values, and it will allow you to execute many different types of queries for which we provide Swagger documentation.

Our API is powered by Amazon OpenSearch, which allows you to query for the more complex/sophisticated use cases.

Example 1: Search across multiple fields for anything matching the word "Nanobody" for the applications filed between 2022 and 2023.

https://api.uspto.gov/api/v1/patent/applications/search

{
  "q": "Nanobody",
  "filters": [
    {
      "name": "applicationMetaData.applicationTypeLabelName",
      "value": [
        "Utility"
      ]
    }
  ],
  "rangeFilters": [
    {
      "field": "applicationMetaData.filingDate",
      "valueFrom": "2022-01-01",
      "valueTo": "2023-12-31"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 25
  },
  "sort": [
    {
      "field": "applicationMetaData.filingDate",
      "order": "Desc"
    }
  ]
}
Example 2: Search for invention title including the word "Nanobody" filed between 2022 and 2023.

https://api.uspto.gov/api/v1/patent/applications/search

{
  "q": "applicationMetaData.invetionTitle:Hair Dryer",
  "filters": [
    {
      "name": "applicationMetaData.applicationTypeLabelName",
      "value": [
        "Design"
      ]
    },
    {
      "name": "applicationMetaData.publicationCategoryBag",
      "value": [
        "Granted/Issued"
      ]
    }
  ],  
  "pagination": {
    "offset": 0,
    "limit": 25
  },
  "sort": [
    {
      "field": "applicationMetaData.filingDate",
      "order": "Desc"
    }
  ],
  "facets": [
    "applicationMetaData.applicationTypeLabelName",
    "applicationMetaData.entityStatusData.businessEntityStatusCategory"
  ]
}
Example 3: ODP Metadata retrieval API that paginates the results and handles HTTP 429 error gracefully (rate limit errors)

To learn about the ODP API Rate Limits, please navigate to the API Rate Limits page.

import requests
import time

SLEEP_AFTER_429 = 0.1
SLEEP_BETWEEN_HTTP = 0
HTTP_RETRY = 10
MAX_RANGE = 10000
LIMIT = 100

api_key = "<YOUR API KEY>"
url = 'https://api.uspto.gov/api/v1/patent/applications/search'
headers = {
    'x-api-key': api_key
}
query_template = {
  "q": None,
  "filters": [
    {
      "name": "applicationMetaData.applicationTypeLabelName",
      "value": ["Utility"]
    },
    {
      "name": "applicationMetaData.publicationCategoryBag",
      "value": ["Pre-Grant Publications - PGPub"]
    },
    {
      "name": "applicationMetaData.applicationStatusDescriptionText",
      "value": ["Non Final Action Mailed"]
    }
  ],
  "rangeFilters": [
    {
      "field": "applicationMetaData.filingDate",
      "valueFrom": "2010-10-01",
      "valueTo": "2023-10-30"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": LIMIT
  },
  "sort": [
    {
      "field": "applicationMetaData.filingDate",
      "order": "Desc"
    }
  ],
  "fields": ["applicationNumberText","applicationMetaData"]
}

application_numbers_api = []

def make_search_request(offset, retry=0):
    query = query_template.copy()
    query['pagination']['offset'] = offset
    response = requests.post(url, headers=headers, json=query)
    if response.status_code == 200:
        data = response.json()
        return [item['applicationNumberText'] for item in data.get('patentFileWrapperDataBag', [])], None
    elif response.status_code == 429:
        if retry < HTTP_RETRY:
            time.sleep(SLEEP_AFTER_429)
            retry += 1
            return make_search_request(offset, retry)
    return None, response

for offset in range(0, MAX_RANGE, LIMIT):  # adjust range and step as needed
    application_numbers, error_response = make_search_request(offset, 0)
    time.sleep(SLEEP_BETWEEN_HTTP)
    if application_numbers is not None:
        application_numbers_api.extend(application_numbers)
    else:
        print(f"request failed with status code {error_response.status_code} for offset: {offset}")
        print(f"response content: {error_response.content}")
        print(f"url causing the error: {url}")
Example 4: ODP Patent File Wrapper document download API code handles the HTTP 429 gracefully (with rate limit errors). To learn about the ODP API Rate Limits, please navigate to the API Rate Limits page.

Please note that some ODP files are large. You may see a significant delay before the file content starts streaming and we recommend setting your maximum time-out to start generating content at 600 seconds. For example, to download file of 100 MB size, you may see a 60 second delay before you see any content streaming. In rare cases of files larger than 250 MB, ODP may still time out after 10 minutes. If you are unable to download large files, send us a message on our Contact us page.

Additionally, ODP uses an HTTP redirect 301 to provide a direct link to download files. Most software libraries will follow redirect automatically or by adding an extra parameter. For example, in Python requests library, you will need to add a parameter allow_redirects=True. In CURL utility, you can follow redirects by adding a “-L” flag.

Change:

response = requests.get(file_url, headers=headers)
to:

response = requests.get(file_url, headers=headers, allow_redirects=True) 
import requests
import time
import random

SLEEP_AFTER_429 = 0.1
SLEEP_BETWEEN_HTTP = 0
HTTP_RETRY = 5
MAX_FILES = 10
total_429 = 0
total_rate = 0

api_key = "<YOUR API KEY>"
url = 'https://api.uspto.gov/api/v1'
apllication_id = "12345678"
meta_data = f"{url}/patent/applications/{apllication_id}/documents"
pdf_file = f"{url}/download/applications/{apllication_id}/FQ0SPLX2PPOPPY5.pdf"
xml_file = f"{url}/download/applications/{apllication_id}/GNDGBKJYPPOPPY5/xmlarchive"
word_file = f"{url}/download/applications/{apllication_id}/GNDGBKJYPPOPPY5/files/Non-Final%20Rejection.DOC"

headers = {
    'x-api-key': api_key
}

files  = [meta_data, pdf_file, xml_file, word_file]

def make_search_request(file_url, retry=0):
    global total_429
    response = requests.get(file_url, headers=headers)
    if response.status_code == 429 and retry < HTTP_RETRY:
        time.sleep(SLEEP_AFTER_429)
        retry += 1
        total_429 += 1
        print(f"Got HTTP 429. Retry number: {retry}")
        return make_search_request(file_url, retry)
    return response

for count in range(0, MAX_FILES):
    file_url = random.choice(files)
    response = make_search_request(file_url, 0)
    time.sleep(SLEEP_BETWEEN_HTTP)
    if response.status_code == 200:
        print(f"Retrieved {count}: {file_url}")
    else:
        print(f"request failed with status code {response.status_code} for url: {file_url}, {response.content}")
If you have any questions or errors, please visit the Support page for assistance.




The Open Data Portal (ODP) API allows you to extract USPTO data at no cost - with several ways to do it. To learn about the ODP API Rate Limits, please visit to the API Rate Limits page.

Before proceeding, you must have an ODP API key in order to access these Swagger UI resources. Once you have obtained an API key, you can pass the API key into a REST API call in the x-api-key header of the request. For more details and steps to generate an API key visit to the Getting Started page.

For example, the request to access patent data for an application might look like as below.

curl -X "GET" "https://api.uspto.gov/api/v1/patent/applications/14412875" -H "X-API-KEY:YOUR_API_KEY"


curl -X "POST" "https://api.uspto.gov/api/v1/patent/applications/search" -H "X-API-KEY:YOUR_API_KEY" -d "{\"q\":\"applicationMetaData.applicationTypeLabelName:Utility\"}"





API rate limits
Was this page helpful?
ODP provides three types of APIs that have their own set of rate limits: Meta data retrieval APIs, Patent File Wrapper Documents API and Bulk Datasets Downloads API.

Meta data retrieval APIs:
For each data product there are a set of meta data retrievals-

Patent File Wrapper API meta data retrieval includes Application Data, Continuity, Transactions, Patent Term Adjustment, Address and Attorney/Agent Information, Assignments, Foreign Priority and Associated Documents.

Bulk Datasets API meta data retrieval includes Product Data.

Final Petition Decisions API meta data retrieval includes Search, Document Data, and Download.

Meta data retrievals are limited to 5 million calls per week for all the APIs in this category combined.

Patent File Wrapper’s Documents API:
The weekly limit for all the APIs under the Patent File Wrapper Documents API is 1,200,000. This means you can make 1.2 million calls per week for the APIs under this category.

Bulk Datasets’ Downloads API:
For the same file downloaded using the Bulk Datasets Downloads API, you are limited to 20 downloads per year using your API key, except for XML files which has a much higher limit

You can download up to 5 files per 10 seconds from the same IP address.

Our files are redirected and digitally signed with a signature expiring in 5 seconds, so be sure to start downloading any redirected files right way.

API rate limit reset
Your weekly quota for Meta data retrieval and Patent File Wrapper Documents APIs will reset on Sunday at midnight Greenwich Time (also known as UTC). After the reset, you will be able to use a full allocated quota again.

We limit all API calls to one API call per API key. You will need to wait until an API call completed until starting a new one. We also advise against using the same API key in applications running in parallel: concurrent API calls with the same key are currently blocked.

API request threshold
Burst: This defines how many requests can be run in parallel per API Key. It is set to 1, meaning you should not run any requests in parallel at all for the same API key.

Rate: This defines how many requests one can submit per second. It is set at 4 to 15, depending on the API call type. For example, if an API call takes 0.1 seconds, you can still submit 10 sequential calls even with the burst limit of 1.

In general, you should design a system that waits for an API call to finish before making the next call using the same API key, as some of the calls require significant resources.

If you submit more than one request at a time or exceed weekly quota, you will get the error message: “HTTP 429 Too Many Requests.” Therefore, it is “best practice” to handle an HTTP 429 error gracefully. We strongly discourage automatic retries, without at least 5 second delay, when you get a HTTP 429 response: this may exacerbate the problem.

Please note these limits are subject to change. Check this page regularly for the most up-to-date information.

If you have any questions or errors, please visit the Support page for assistance.


Transition guide - Patent Examination Data System (PEDS)
Was this page helpful?
info_icon
Want to view the latest PEDS to Open Data Portal (ODP) PEDS API mapping? Download our PEDS API to ODP API mapping page.
As of March 14, 2025, Patent Examination Data System (PEDS) is no longer available. To access publicly available records of USPTO patent applications or patent filing status, users can access Open Data Portal’s Patent File Wrapper feature.

Use this transition guide to get you accustomed to the Patent File Wrapper interface and utilizing the Application Programming Interfaces (APIs).

Here are some key points to consider as you are migrating your API from PEDS to ODP:

PEDS supported data starting from 1900. ODP includes data from 2001 to present
Data before 2001 does not include comprehensive data, and records need to be completed. This data does not provide easy dissemination to users and allows us to focus our efforts on enhancing ODP capabilities.
To retrieve data prior to January 2001 that you previously found on PEDS, you can visit the Patent Center (for data similar to what is found in ODP) or find the static files in Bulk Data Directory’s Patent Examination Data System (Bulk Datasets) - XML and Patent Examination Data System (Bulk Datasets) - JSON
PEDS had datasets in XML and JSON format for download. ODP only supports JSON format via API
For any API calls using XML format, your program must be switched to retrieve JSON format only.
PEDS did not require an API key, but ODP requires users to get their unique API key to access data
Learn how to get your API Key on the Getting Started page.
The link for your API Call will need to change
PEDS API was "https://ped.uspto.gov/api/"
ODP API link will be "https://api.uspto.gov/"
Free form search is supported on ODP
PEDS did not support free-form search where a value is searched against all searchable datasets.
ODP provides more attributes
ODP provides a more refined data structure and additional attributes that were not supported in PEDS. The attribute list and details can be found in the API Documentation page and the API Schema Document.



Application Data
Was this page helpful?
The Application Data section contains key bibliographic information found on the front page of granted patents and published patent applications. Use this endpoint when you want application data for a specific patent application whose application number you know. You can test APIs right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/meta-data

e.g. https://api.uspto.gov/api/v1/patent/applications/16330077/meta-data

Returns application data for application number

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
PatentFileWrapperDataBag	Patent File Wrapper data.	N/A
  applicationNumberText	The unique number assigned by the USPTO to a patent application when it is filed.	String
entityStatusData	Entity status data	Entity status
  smallEntityStatusIndicator	Small entity status indicator	boolean
  businessEntityStatusCategory	Status of business The large-or-small-entity payment status of the APPLICATION PATENT CASE at the time of the small entity status event and thereafter until the occurrence of a later small entity status event for the APPLICATION PATENT CASE. entity being established for the purpose of paying a fee such as a filing fee and a maintenance fee	String
publicationDateBag	Publication dates	Array of dates
publicationSequenceNumberBag	Publication sequence number	N/A
publicationCategoryBag	One or more of the publication category	String
  docketNumber	Docket number	String
applicationMetaData	MetaData of the application.	N/A
  firstInventorToFileIndicator	First inventor to file indicator	String
  firstApplicantName	First applicant name	String
  firstInventorName	First inventory name	String
  applicationConfirmationNumber	The application's confirmation number	String
  applicationStatusDate	The date of the application status	Date
  applicationStatusDescriptionText	status of the application; values: new = new application	String
  filingDate	Filing or 371(c) date on which a patent application was filed and received in the USPTO.	Date
  effectiveFilingDate	The date according to USPTO criteria that the patent case qualified as having been 'filed'. The effective filing date is the same or later than the filingDate. The effectiveFilingDate is not the date of any priority or benefit claim to a prior filed application. For most applications the effectiveFilingDate is the date they filed electronically, or the date the USPTO received the mail in the USPTO mailroom.	Date
  grantDate	The date a patent was granted.	String
  groupArtUnitNumber	A working unit responsible for a cluster of related patent art. Generally, staffed by one supervisory patent examiner (SPE) and a number o patent examiners who determine patentability on applications for a patent. Group Art Units are currently identified by a four digit number, i.e., 1644.	String
  applicationTypeCode	The specific value that indicates if the received patent application is considered a domestic application at the National Stage or is submitted as a Patent Cooperative Treaty (PCT) application.	String
  applicationTypeLabelName	The label for the application type.	String
  applicationTypeCategory	The category of the application	String
  inventionTitle	Title of invention/application: The clear and concise technical description of the invention as provided by the patent applicant.	String
  patentNumber	The number that uniquely identifies an issued patent. It is also the document number in USTPO published Redbook and the Official Gazette. This number can be for an originally-issued patent or a re-issued patent. It will not be for a Re-exam Certificate, a Correction Certificate, a SIR, or a notice of a request for a Re-exam or a Reissue. This number is equivalent to WIPO ST.9 as INID 11. 5012717	String
  applicationStatusCode	Application status code	Number
  earliestPublicationNumber	Earliest publication number	String
  earliestPublicationDate	The first publication date	Date
  pctPublicationNumber	PCT publication number	String
  pctPublicationDate	PCT publication date	String
  internationalRegistrationPublicationDate	The date of publication by the International Bureau of an international registration of an industrial design	String
  internationalRegistrationNumber	The number assigned by the International Bureau to an international registration upon registering the industrial design in the International Register	String
  examinerNameText	Examiner's name	String
  class	Class	String
  subclass	Subclass	String
  uspcSymbolText	uspcSymbolText	String
  customerNumber	A unique number created by the USPTO and is used in lieu of a physical address	Number
  nationalStageIndicator	National Stage indicator.	Boolean
cpcClassificationBag	CPC classification data collection	N/A
applicantBag	List of applicants	N/A
  applicantNameText	Applicant name	String
  firstName	First name of applicant	String
  middleName	Middle name of applicant	String
  lastName	Last name of application	String
  preferredName	Preferred name of applicant	String
  namePrefix	Name prefix	String
  nameSuffix	Name suffix	String
  countryCode	Country code	String
correspondenceAddressBag	Correspondence address data	N/A
  nameLineOneText	Name first line	String
  nameLineTwoText	Name second line	String
  geographicRegionName	Geographic region name	String
  geographicRegionCode	Geographic region code	String
  cityName	City name	String
  countryCode	Country code	String
  countryName	Country Name	String
  postalAddressCategory	Postal category such as 'Residential' or 'Commercial'	String
inventorBag	All the inventors associated to application.	N/A
  firstName	First name of inventor	String
  middleName	Middle name of inventor	String
  lastName	Last name of inventor	String
  namePrefix	Name prefix	String
  nameSuffix	Name suffix	String
  preferredName	Preferred name of inventor	String
  countryCode	Country code	String
  inventorNameText	Inventor full name	String
correspondenceAddressBag	Correspondence address data	N/A
  nameLineOneText	Name line one	String
  nameLineTwoText	Name line two	String
  geographicRegionName	Geographic region name	String
  geographicRegionCode	Geographic region code	String
  cityName	City name	String
  countryCode	Country code	String
  countryName	Country name	String
  postalAddressCategory	Postal category such as 'Residential' or 'Commercial'	String









Conduct a search of all patent application bibliographic/front page and patent relevant data fields. This data is refreshed daily.

Use this endpoint if you are interested in searching across multiple patents or applications. For example, you want to return all patents and applications that match your search term, such as Utility or Design. You can also use multiple search terms, such as “Patented AND Abandoned.” You can use any combination of the 100+ data attributes available and documented below.

Note: The other endpoints (such as Application Data, Continuity, etc.) should be used when you're using a specific application number to find more detailed information. For example, you want to return all the relevant application data about Application #14412875 or all continuity data for Application #10588979.

Other details for using the Search endpoint:

If you don’t specify the field in which you want us to look for this search term, we will look for it across all application data (inventionTitle, patentNumber, applicationTypeLabelName, correspondenceAddressBag etc.) and return any matching patents or applications.

If you don’t specify which attributes you would like to see in the response related to the search term(s), it returns all data attributes.

All search syntaxes are applicable to this endpoint, meaning any number of combinations is possible. Some example requests are below, but for more information, view the Simplified Syntax documentation that is linked in the Open Data Portal API page. You can also test the API right away in Swagger UI swagger icon.

You can download the JSON Schema file to parse the JSON responses returned by the APIs.

GET https://api.uspto.gov/api/v1/patent/applications/search

Returns a list of all patents and applications that match your search term.

Note: API Key is required. Obtain an API key.

POST See Swagger documentation

Returns a list of all patents and applications that match your search term.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
PatentFileWrapperDataBag	Patent File Wrapper data.	N/A
  applicationNumberText	The unique number assigned by the USPTO to a patent application when it is filed.	String
applicationMetaData	MetaData of the application.	N/A
  firstInventorToFileIndicator	The first inventor to file (First Inventor to File- FITF) provision of the America Invents Act (AIA) transitions the U.S. to a first-inventor-to-file system from a first-to-invent system.	String
  nationalStageIndicator	National Stage indicator.	Boolean
  smallEntityStatusIndicator	Small entity status indicator.	Boolean
  docketNumber	An identifier assigned by a non-USPTO interest to an application patent case. The identifier is assigned by the person filing the application (applicant or the legal representative of the applicant) to identify the application internally on customer side. It's optional for the customer.	String
  firstApplicantName	Name of the Applicant with Rank One. Listed as first applicant in the patent application.	String
  firstInventorName	Name of the inventor with Rank One. Listed as first inventor in the patent application.	String
  applicationConfirmationNumber	A four-digit number that is assigned to each newly filed patent application. The confirmation number, in combination with the application number, is used to verify the accuracy of the application number placed on correspondence /filed with the office to avoid mis identification of an application due to a transposition error (misplaced digits) in the application number. The office recommends that applicants include the application's confirmation number (in addition to the application number) on all correspondence submitted to the office concerning the application.	Number
  applicationStatusDate	Application status date.	Date
  applicationStatusDescriptionText	Status of the application; values: new = new application	String
  filingDate	Filing or 371(c) date on which a patent application was filed and received in the USPTO.	Date
  effectiveFilingDate	The date according to USPTO criteria that the patent case qualified as having been 'filed'. The effective filing date is the same or later than the filingDate. The effectiveFilingDate is not the date of any priority or benefit claim to a prior filed application. For most applications the effectiveFilingDate is the date they filed electronically, or the date the USPTO received the mail in the USPTO mailroom.	Date
  grantDate	The date a patent was granted.	Date
  groupArtUnitNumber	A working unit responsible for a cluster of related patent art. Generally, staffed by one supervisory patent examiner (SPE) and a number of patent examiners who determine patentability on applications for a patent. Group Art Units are currently identified by a four digit number, i.e., 1642.	String
  applicationTypeCode	The specific value that indicates if the received patent application is considered a domestic application at the National Stage or is submitted as a Patent Cooperative Treaty (PCT) application.	String
  applicationTypeLabelName	The label for the application type.	String
  applicationTypeCategory	The category of the application	String
  inventionTitle	Title of invention/application: The clear and concise technical description of the invention as provided by the patent applicant.	String
  patentNumber	The unique number assigned by the USPTO to a granted/issued patent. It is also the document number in the USTPO-published Redbook and the Official Gazette. This number can be for an originally-issued patent or a re-issued patent. It will not be for a Re-exam Certificate, a Correction Certificate, a SIR, or a notice of a request for a Re-exam or a Reissue. This number is equivalent to WIPO ST.9 as INID 11. 5012717.	String
  applicationStatusCode	This data element classifies the application by its status relative to the total application process.	String
  businessEntityStatusCategory	Status of business The large-or-small-entity payment status of the APPLICATION PATENT CASE at the time of the small entity status event and thereafter until the occurrence of a later small entity status event for the APPLICATION PATENT CASE. entity being established for the purpose of paying a fee such as a filing fee and a maintenance fee	String
  earliestPublicationNumber	Earliest publication number.	String
  earliestPublicationDate	Earliest publication date.	Date
  pctPublicationNumber	PCT publication number	String
  pctPublicationDate	PCT publication date	String
publicationSequenceNumberBag	Contains a number assigned to the publication of patent applications filed on or after November 29, 2000. It includes the year, followed by a seven digit number, followed by a kind code. Example: 200011234567A1.	N/A
correspondenceAddressBag	All address lines associated with applicant or inventor correspondence, depending on which bag it falls in.	N/A
  nameLineOneText	First line of name associated with correspondence address.	String
  nameLineTwoText	Second line of name associated with correspondence address, if applicable.	String
  addressLineOneText	First line of address associated with correspondence address.	String
  addressLineTwoText	Second line of address associated with correspondence address, if applicable.	String
  geographicRegionName	Geographic Region Name, e.g., state.	String
  geographicRegionCode	Geographic region code.	String
  postalCode	Postal Code.	String
  cityName	City Name.	String
  countryCode	Country code.	String
  countryName	Country name.	String
  postalAddressCategory	Postal address category.	String
customerNumber	A unique number created by the USPTO and is used in lieu of a physical address.	Number
cpcClassificationBag	All the CPCs associated to application.	N/A
applicantBag	All applicants associated to application.	N/A
  applicantNameText	Applicant name	String
  firstName	First Name.	String
  middleName	Middle name.	String
  lastName	Last Name.	String
  preferredName	Preferred name.	String
  namePrefix	Name prefix.	String
  nameSuffix	Name suffix.	String
  countryCode	Country code.	String
correspondenceAddressBag	All address lines associated with applicant or inventor correspondence, depending on which bag it falls in.	N/A
  nameLineOneText	First line of name associated with correspondence address.	String
  nameLineTwoText	Second line of name associated with correspondence address, if applicable.	String
  geographicRegionName	Geographic Region Name, e.g., state.	String
  geographicRegionCode	Geographic region code.	String
  cityName	City Name.	String
  countryCode	Country code.	String
  countryName	Country name.	String
  postalAddressCategory	Postal address category.	String
inventorBag	All the inventors associated to application.	N/A
  firstName	First Name.	String
  middleName	Middle name.	String
  lastName	Last Name.	String
  preferredName	Preferred name.	String
  namePrefix	Name prefix.	String
  nameSuffix	Name suffix.	String
  countryCode	Country code.	String
  inventorNameText	Inventor Name.	String
correspondenceAddressBag	All address lines associated with applicant or inventor correspondence, depending on which bag it falls in.	N/A
  nameLineOneText	First line of name associated with correspondence address.	String
  nameLineTwoText	Second line of name associated with correspondence address, if applicable.	String
  geographicRegionName	Geographic Region Name, e.g., state.	String
  geographicRegionCode	Geographic region code.	String
  cityName	City Name.	String
  countryCode	Country code.	String
  countryName	Country name.	String
  postalAddressCategory	Postal address category.	String
assignmentBag	The collection of assignment data	N/A
  reelNumber	1-6 digit number identifies the reel number to be used to locate the assignment on microfilm.	Number
  frameNumber	1-4 digit number that identifies the frame number to be used to locate the first image (page) of the assignment on microfilm.	Number
  reelAndFrameNumber	1-6 digit number identifies the reel number to be used to locate the assignment on microfilm. / 1-4 digit number that identifies the frame number to be used to locate the first image (page) of the assignment on microfilm.	String
  pageTotalQuantity	The total number of pages comprising the document	Number
  assignmentDocumentLocationURI	The Document Location URI	String
  assignmentReceivedDate	The date an assignment was received. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
  assignmentRecordedDate	Identifies when the assignment was recorded in the USPTO. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
  imageAvailableStatusCode	code to indicate the availability of the image	boolean
  assignmentMailedDate	The date an assignment request was mailed to the office or received by the office. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
  conveyanceText	Contains textual description of the interest conveyed or transaction recorded.	String
assignorBag	Collection of assignors/details related to the assignor(s).	N/A
  assignorName	A party that transfers its interest and right to the patent to the transferee (assignee) or the party receiving the patent.	String
  executionDate	Identifies the date from the supporting legal documentation that the assignment was executed. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
assigneeBag	Collection of assignees/details related to the assignee(s).	N/A
  assigneeNameText	A person or entity that has the property rights to the patent, as a result of being the recipient of a transfer of a patent application or patent grant. Refers to ST.9 INID Code 73.	String
assigneeAddress	Assignee address data.	N/A
  addressLineOneText	First line of address.	String
  addressLineTwoText	Second line of address.	String
  addressLineThreeText	Third line of address associated with the assignee.	String
  addressLineFourText	Fourth line of address associated with the assignee.	String
  cityName	Name of the city	String
  countryOrStateCode	Country or state code	String
  ictStateCode	International code for the state/region of the assignee (USPTO format)	String
  ictCountryCode	International code for the country of the assignee (USPTO format)	String
  geographicRegionName	Geographic region name.	String
  geographicRegionCode	Geographic region code.	String
  countryName	Country name.	String
  postalCode	Postal code.	String
correspondenceAddress	Correspondence data collection	N/A
  correspondentNameText	The name of the correspondent	String
  addressLineOneText	Address line one.	String
  addressLineTwoText	Address line two.	String
  addressLineThreeText	Address line three, if existing	String
  addressLineFourText	Address line four, if existing	String
domesticRepresentative	The address of the domestic representative	N/A
  name	The domestic representative name.	String
  addressLineOneText	First line of address associated with the correspondent.	String
  addressLineTwoText	Second line of address associated with the correspondent.	String
  addressLineThreeText	Third line of address associated with the correspondent.	String
  addressLineFourText	Fourth line of address associated with the correspondent, if applicable.	String
  cityName	Name of the city	String
  postalCode	Postal code	String
  geographicRegionName	Geographic region name	String
  countryName	Country name.	String
  emailAddress	Email address of the representative.	Date
recordAttorney	Details of the attorney or agent associated with an application/patent.	N/A
customerNumberCorrespondenceData	Correspondence Address of the application inherited from the Customer.	N/A
  patronIdentifier	The unique identifier of the patron	String
  organizationStandardName	Organization standard name	String
powerOfAttorneyAddressBag	Power of attorney address data collection.	N/A
  nameLineOneText	First line of name associated with attorney/agent correspondence address.	String
  addressLineOneText	First line of the address	String
  addressLineTwoText	Second line of the address	String
  geographicRegionName	Geographic region name	String
  geographicRegionCode	Geographic region code	String
  postalCode	Postal code	String
  cityName	City name	String
  countryCode	Country code	String
  countryName	Country name	String
telecommunicationAddressBag	List of telecommunication addresses, such as the phone number(s) associated with the aforementioned attorney or agent.	N/A
  telecommunicationNumber	Telecommunication number, such as the phone number associated with the aforementioned attorney or agent.	String
  extensionNumber	Telephone extension number.	String
  telecomTypeCode	Usage type category, such as the type of phone number associated with the aforementioned attorney or agent.	String
attorneyBag	Data on file for all attorneys or agents associated with the application.	N/A
  firstName	First Name.	String
  middleName	Middle Name.	String
  lastName	Last Name.	String
  namePrefix	Name prefix.	String
  nameSuffix	Name suffix.	String
  registrationNumber	Registration number.	Number
  activeIndicator	Status of whether attorney is active or inactive.	Boolean
  registeredPractitionerCategory	Practitioner category	String
telecommunicationAddressBag	List of telecommunication addresses, such as the phone number(s) associated with the aforementioned attorney or agent.	N/A
  telecommunicationNumber	Telecommunication number, such as the phone number associated with the aforementioned attorney or agent.	String
  extensionNumber	Telephone extension number.	Number
  telecomTypeCode	Usage type category, such as the type of phone number associated with the aforementioned attorney or agent.	String
foreignPriorityBag	Contains information about relevant foreign priority.	N/A
  ipOfficeName	The complete, non abbreviated name of the ipOfficeName designated for a country according to the International Organization for Standardization (ISO) under International Standard 3166-1.	String
  filingDate	The date on which a priority claim was filed.	Date
  applicationNumberText	The unique number assigned by the USPTO to a patent application when it is filed.	String
parentContinuityBag	All continuity details related to the parent application.	N/A
  firstInventorToFileIndicator	America Invents Act (AIA) indicator, which indicates first inventor to file.	Boolean
  parentApplicationStatusCode	This data element classifies the application by its status relative to the total application process.	Number
  parentPatentNumber	The number that uniquely identifies an issued patent. It is also the document number in the USTPO-published Redbook and the Official Gazette. This number can be for an originally-issued patent or a re-issued patent. It will not be for a Re-exam Certificate, a Correction Certificate, a SIR, or a notice of a request for a Re-exam or a Reissue. This number is equivalent to WIPO ST.9 as INID 11. 5012717.	String
  parentApplicationStatusDescriptionText	Status of the parent or child application, depending on which bag it falls under; values: new = new application, patented case, patent expired...	String
  parentApplicationfilingDate	Date on which a patent application was filed and received in the USPTO.	Date
  parentApplicationNumberText	Application number of the parent application, which is the unique value assigned by the USPTO to a patent application upon receipt.	String
  childApplicationNumberText	Application number of the child application, which is the unique value assigned by the USPTO to a patent application upon receipt.	String
  claimParentageTypeCode	Claim parentage type code.	String
  claimParentageTypeCodeDescriptionText	Claim Parentage Type Code Description	String
childContinuityBag	All continuity details related to the child application	N/A
  childApplicationStatusCode	Application status code.	String
  parentApplicationNumberText	Parent application number for this child application.	String
  childApplicationNumberText	Application number of the child application, which is the unique value assigned by the USPTO to a patent application upon receipt.	String
  childApplicationStatusDescriptionText	Status of the parent or child application, depending on which bag it falls under; values: new = new application, patented case, patent expired...	String
  childApplicationfilingDate	Date on which a patent application was filed and received in the USPTO.	Date
  firstInventorToFileIndicator	America Invents Act (AIA) indicator, which indicates first inventor to file.	Boolean
  childPatentNumber	The number that uniquely identifies an issued patent. It is also the document number in the USTPO-published Redbook and the Official Gazette. This number can be for an originally-issued patent or a re-issued patent. It will not be for a Re-exam Certificate, a Correction Certificate, a SIR, or a notice of a request for a Re-exam or a Reissue. This number is equivalent to WIPO ST.9 as INID 11. 5012717.	String
  claimParentageTypeCode	Claim parentage type code.	String
  claimParentageTypeCodeDescriptionText	Description of claim parentage type	String
patentTermAdjustmentData	Patent term adjustment data.	N/A
    aDelayQuantity	This entry reflects adjustments to the term of the patent based upon USPTO delays pursuant to 35 U.S.C. § 154(b)(1)(A)(i)-(iv) and the implementing regulations 37 CFR 1.702(a) & 37 CFR 1.703(a). An "A" delay may occur prior to the notice of allowance and be included in the PTA determination accompanying the notice of allowance or may occur after the entry or mailing of the notice of allowance and be included in the PTA determination in the issue notification letter.	Number
    adjustmentTotalQuantity	This entry reflects the summation of the following entries: NONOVERLAPPING USPTO DELAYS (+/or – USPTO MANUAL ADJUSTMENTS) – APPLICANT DELAYS. It is noted that the TOTAL PTA CALCULATION determined at the time of the notice of allowance will not reflect PALM entries that are entered after the entry or mailing of the notice of allowance.	Number
    applicantDayDelayQuantity	This entry reflects adjustments of the patent term due to the Applicant's failure to engage in reasonable efforts to conclude prosecution of the application for the cumulative period in excess of three months. See 35 U.S.C. § 154(b)(2)(C)(ii) and implementing regulation 37 CFR 1.704(b). The entry also reflects additional Applicant's failure to engage in reasonable efforts to conclude prosecution of the application. See 35 U.S.C. § 154(b)(2)(C)(iii) and implementing regulations 37 CFR 1.704(c)(1)-(11).	Number
    bDelayQuantity	This entry reflects adjustments to the term of the patent based upon the patent failing to issue within three years of the actual filing date of the application in the United States. See 35 U.S.C. § 154(b) and implementing regulations 37 CFR 1.702(b) & 1.703(b). "B" delay is always calculated at the time that the issue notification letter is generated and an issue date has been established.	Number
    cDelayQuantity	This entry reflects adjustments to the term of the patent based upon USPTO delays pursuant to 35 U.S.C. § 154(C)(i)-(iii) and implementing regulations 37 CFR 1.702 (c)-(e) & 1.703(c)-(e). These delays include delays caused by interference proceedings, secrecy orders, and successful appellate reviews.	Number
    overlappingDayQuantity	Patent term adjustment overlapping days quantity number that reflects the calculation of overlapping delays consistent with the federal circuit's interpretation.	Number
  nonOverlappingDayQuantity	Patent term adjustment non overlapping days quantity number of overall summation of the USPTO delays minus any overlapping days.	Number
    patentTermAdjustmentHistoryDataBag	The recordation of patent case actions that are involved in the patent term adjustment calculation.	N/A
    applicantDayDelayQuantity	This entry reflects adjustments of the patent term due to the Applicant's failure to engage in reasonable efforts to conclude prosecution of the application for the cumulative period in excess of three months. See 35 U.S.C. § 154(b)(2)(C)(ii) and implementing regulation 37 CFR 1.704(b). The entry also reflects additional Applicant's failure to engage in reasonable efforts to conclude prosecution of the application. See 35 U.S.C. § 154(b)(2)(C)(iii) and implementing regulations 37 CFR 1.704(c)(1)-(11).	Number
      eventDate	The date that the symbol was assigned to the patent document.	Date
      eventDescriptionText	event description.	String
      eventSequenceNumber	Case action sequence number.	Number
      ipOfficeDayDelayQuantity	Number of days the UPSTO personnel adjusting the calculation to increase or decrease the patent term adjustment based upon a request for reconsideration of the patent term adjustment.	Number
      originatingEventSequenceNumber	Start sequence number.	Number
      ptaPTECode	PTA or PTE code	String
eventDataBag	Details of the contents of all transactions on an application/patent.	N/A
  eventCode	The unique reference value (number and letters) for an application/patent transaction.	String
  eventDescriptionText	Description of the Transaction's code.	String
  eventDate	The date the patent case action was recorded.	Date
pgpubDocumentMetaData	Details of PgPub document meta data.	N/A
  zipFileName	Zip file name	String
  productIdentifier	Product identifier.	String
  fileLocationURI	File location URI.	String
  fileCreateDateTime	The date file was created.	Date
  xmlFileName	XML file name.	String
grantDocumentMetaData	Grant document meta data.	N/A
  zipFileName	Zip file name	String
  productIdentifier	Product identifier.	String
  fileLocationURI	File location URI.	String
  fileCreateDateTime	The date file was created.	Date
  xmlFileName	XML file name.	String
lastIngestionDateTime	Date time when application was last modified.	Date


The Application Data section contains key bibliographic information found on the front page of granted patents and published patent applications. Use this endpoint when you want application data for a specific patent application whose application number you know. You can test APIs right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/meta-data

e.g. https://api.uspto.gov/api/v1/patent/applications/16330077/meta-data

Returns application data for application number

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
PatentFileWrapperDataBag	Patent File Wrapper data.	N/A
  applicationNumberText	The unique number assigned by the USPTO to a patent application when it is filed.	String
entityStatusData	Entity status data	Entity status
  smallEntityStatusIndicator	Small entity status indicator	boolean
  businessEntityStatusCategory	Status of business The large-or-small-entity payment status of the APPLICATION PATENT CASE at the time of the small entity status event and thereafter until the occurrence of a later small entity status event for the APPLICATION PATENT CASE. entity being established for the purpose of paying a fee such as a filing fee and a maintenance fee	String
publicationDateBag	Publication dates	Array of dates
publicationSequenceNumberBag	Publication sequence number	N/A
publicationCategoryBag	One or more of the publication category	String
  docketNumber	Docket number	String
applicationMetaData	MetaData of the application.	N/A
  firstInventorToFileIndicator	First inventor to file indicator	String
  firstApplicantName	First applicant name	String
  firstInventorName	First inventory name	String
  applicationConfirmationNumber	The application's confirmation number	String
  applicationStatusDate	The date of the application status	Date
  applicationStatusDescriptionText	status of the application; values: new = new application	String
  filingDate	Filing or 371(c) date on which a patent application was filed and received in the USPTO.	Date
  effectiveFilingDate	The date according to USPTO criteria that the patent case qualified as having been 'filed'. The effective filing date is the same or later than the filingDate. The effectiveFilingDate is not the date of any priority or benefit claim to a prior filed application. For most applications the effectiveFilingDate is the date they filed electronically, or the date the USPTO received the mail in the USPTO mailroom.	Date
  grantDate	The date a patent was granted.	String
  groupArtUnitNumber	A working unit responsible for a cluster of related patent art. Generally, staffed by one supervisory patent examiner (SPE) and a number o patent examiners who determine patentability on applications for a patent. Group Art Units are currently identified by a four digit number, i.e., 1644.	String
  applicationTypeCode	The specific value that indicates if the received patent application is considered a domestic application at the National Stage or is submitted as a Patent Cooperative Treaty (PCT) application.	String
  applicationTypeLabelName	The label for the application type.	String
  applicationTypeCategory	The category of the application	String
  inventionTitle	Title of invention/application: The clear and concise technical description of the invention as provided by the patent applicant.	String
  patentNumber	The number that uniquely identifies an issued patent. It is also the document number in USTPO published Redbook and the Official Gazette. This number can be for an originally-issued patent or a re-issued patent. It will not be for a Re-exam Certificate, a Correction Certificate, a SIR, or a notice of a request for a Re-exam or a Reissue. This number is equivalent to WIPO ST.9 as INID 11. 5012717	String
  applicationStatusCode	Application status code	Number
  earliestPublicationNumber	Earliest publication number	String
  earliestPublicationDate	The first publication date	Date
  pctPublicationNumber	PCT publication number	String
  pctPublicationDate	PCT publication date	String
  internationalRegistrationPublicationDate	The date of publication by the International Bureau of an international registration of an industrial design	String
  internationalRegistrationNumber	The number assigned by the International Bureau to an international registration upon registering the industrial design in the International Register	String
  examinerNameText	Examiner's name	String
  class	Class	String
  subclass	Subclass	String
  uspcSymbolText	uspcSymbolText	String
  customerNumber	A unique number created by the USPTO and is used in lieu of a physical address	Number
  nationalStageIndicator	National Stage indicator.	Boolean
cpcClassificationBag	CPC classification data collection	N/A
applicantBag	List of applicants	N/A
  applicantNameText	Applicant name	String
  firstName	First name of applicant	String
  middleName	Middle name of applicant	String
  lastName	Last name of application	String
  preferredName	Preferred name of applicant	String
  namePrefix	Name prefix	String
  nameSuffix	Name suffix	String
  countryCode	Country code	String
correspondenceAddressBag	Correspondence address data	N/A
  nameLineOneText	Name first line	String
  nameLineTwoText	Name second line	String
  geographicRegionName	Geographic region name	String
  geographicRegionCode	Geographic region code	String
  cityName	City name	String
  countryCode	Country code	String
  countryName	Country Name	String
  postalAddressCategory	Postal category such as 'Residential' or 'Commercial'	String
inventorBag	All the inventors associated to application.	N/A
  firstName	First name of inventor	String
  middleName	Middle name of inventor	String
  lastName	Last name of inventor	String
  namePrefix	Name prefix	String
  nameSuffix	Name suffix	String
  preferredName	Preferred name of inventor	String
  countryCode	Country code	String
  inventorNameText	Inventor full name	String
correspondenceAddressBag	Correspondence address data	N/A
  nameLineOneText	Name line one	String
  nameLineTwoText	Name line two	String
  geographicRegionName	Geographic region name	String
  geographicRegionCode	Geographic region code	String
  cityName	City name	String
  countryCode	Country code	String
  countryName	Country name	String
  postalAddressCategory	Postal category such as 'Residential' or 'Commercial'	String


Continuity
Was this page helpful?
The Continuity section contains continuity details for the patent, including parent and/or child continuity data. Continuity Data includes Parent Continuity Data and Child Continuity Data. Use this endpoint when you want continuity data for a specific patent application whose application number you know. You can test the API right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/continuity

Returns a list of all patents and applications that match your search term.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
parentContinuityBag	All continuity details related to the parent application.	N/A
  parentApplicationStatusCode	This data element classifies the application by its status relative to the total application process.	Number
  firstInventorToFileIndicator	First Inventor on file indicator.	Boolean
  claimParentageTypeCode	Claim parentage type code.	String
  claimParentageTypeCodeDescriptionText	Claim parentage type code description.	String
  parentApplicationStatusDescriptionText	Status of the parent application, depending on which bag it falls under; values: new = new application, patented case, patent expired...	String
  parentApplicationNumberText	Application number of the parent application, which is the unique value assigned by the USPTO to a patent application upon receipt.	String
  parentApplicationFilingDate	Date on which a patent application was filed and received in the USPTO.	Date
  parentPatentNumber	The number that uniquely identifies an issued patent. It is also the document number in the USTPO-published Redbook and the Official Gazette. This number can be for an originally-issued patent or a re-issued patent. It will not be for a Re-exam Certificate, a Correction Certificate, a SIR, or a notice of a request for a Re-exam or a Reissue. This number is equivalent to WIPO ST.9 as INID 11. 5012717.	String
childContinuityBag	All continuity details related to the parent application	N/A
  firstInventorToFileIndicator	First Inventor on file indicator.	Boolean
  childApplicationStatusDescriptionText	Status of the child application, depending on which bag it falls under; values: new = new application, patented case, patent expired...	String
  claimParentageTypeCode	Claim parentage type code.	String
  childApplicationStatusCode	This data element classifies the application by its status relative to the total application process.	Number
  claimParentageTypeCodeDescriptionText	Claim parentage type code description.	String
  parentApplicationNumberText	Application number of the parent application, which is the unique value assigned by the USPTO to a patent application upon receipt.	String
  childApplicationFilingDate	Date on which a patent application was filed and received in the USPTO.	Date
  childApplicationNumberText	Application number of the child application, which is the unique value assigned by the USPTO to a patent application upon receipt.	String


Documents
Was this page helpful?
The Documents section contains details on documents attached to the patent application, as well as options for downloading the documents. This includes documents under all codes (Examiner’s Amendment Communication, Printer Rush, IDS Filed, Application is Now Complete, PTA 36 months). Use this endpoint when you want documents related to a specific patent application whose application number you know. You can test the API right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/documents

Returns document meta-data along with document download URI for supplied application number.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
documentBag	Details of the documents related to an application.	N/A
  applicationNumberText	The unique number assigned by the USPTO to a patent application upon receipt when it is filed.	String
  officialDate	The date correspondence is received at the USPTO, either through the mail room or via the Internet.	Date
  documentIdentifier	A unique identifier for a document stored in the repository.	String
  documentCode	The unique reference value (number and letters) for an application/patent document.	String
  documentCodeDescriptionText	Document code's description.	String
  directionCategory	Category for the document type (Incoming, Outgoing.	String
downloadOptionBag	Details about download options for the documents.	N/A
  mimeTypeIdentifier	Document type identifier (e.g., PDF/XML/Docx)	String
  downloadUrl	Link to download	String
  pageTotalQuantity	Total number of pages in the document.	Number



Transactions
Was this page helpful?
The transactions section contains additional information concerning the transaction activity that has occurred for each patent application. This includes details on the date of the transaction, code (Examiner’s Amendment Communication, Printer Rush, IDS Filed, Application is Now Complete, PTA 36 months), and transaction description. Use this endpoint when you want transaction data related to a specific patent application whose application number you know. You can test the API right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/transactions

Returns all transactions associated for supplied application.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
eventDataBag	Details of the contents of all transactions on an application/patent.	N/A
  eventCode	A short text field that denotes the A16 CT codes.	String
  eventDescriptionText	A text field that denotes the use or function of the activity	String
  eventDate	The date of the legal status change event.	Date



Patent Term Adjustment
Was this page helpful?
The Patent Term Adjustment section provides additional information concerning the patent term adjustment that has occurred for each patent. Use this endpoint when you want patent term adjustment data related to a specific patent application whose application number you know. You can test APIs right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/adjustment

Returns adjustment data for supplied application number.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
patentTermAdjustmentData	Patent term adjustment data.	N/A
  applicantDayDelayQuantity	This entry reflects adjustments of the patent term due to the Applicant's failure to engage in reasonable efforts to conclude prosecution of the application for the cumulative period in excess of three months. See 35 U.S.C. § 154(b)(2)(C)(ii) and implementing regulation 37 CFR 1.704(b). The entry also reflects additional Applicant's failure to engage in reasonable efforts to conclude prosecution of the application. See 35 U.S.C. § 154(b)(2)(C)(iii) and implementing regulations 37 CFR 1.704(c)(1)-(11).	Number
  overlappingDayQuantity	Patent term adjustment overlapping days quantity number that reflects the calculation of overlapping delays consistent with the federal circuit's interpretation.	Number
  ipOfficeAdjustmentDelayQuantity	IP office adjustment delay summation	Number
  cDelayQuantity	This entry reflects adjustments to the term of the patent based upon USPTO delays pursuant to 35 U.S.C. § 154(C)(i)-(iii) and implementing regulations 37 CFR 1.702 (c)-(e) & 1.703(c)-(e). These delays include delays caused by interference proceedings, secrecy orders, and successful appellate reviews.	Number
  adjustmentTotalQuantity	This entry reflects the summation of the following entries: NONOVERLAPPING USPTO DELAYS (+/or – USPTO MANUAL ADJUSTMENTS) – APPLICANT DELAYS. It is noted that the TOTAL PTA CALCULATION determined at the time of the notice of allowance will not reflect PALM entries that are entered after the entry or mailing of the notice of allowance.	Number
  bDelayQuantity	This entry reflects adjustments to the term of the patent based upon the patent failing to issue within three years of the actual filing date of the application in the United States. See 35 U.S.C. § 154(b) and implementing regulations 37 CFR 1.702(b) & 1.703(b). "B" delay is always calculated at the time that the issue notification letter is generated and an issue date has been established.	Number
  aDelayQuantity	This entry reflects adjustments to the term of the patent based upon USPTO delays pursuant to 35 U.S.C. § 154(b)(1)(A)(i)-(iv) and the implementing regulations 37 CFR 1.702(a) & 37 CFR 1.703(a). An "A" delay may occur prior to the notice of allowance and be included in the PTA determination accompanying the notice of allowance or may occur after the entry or mailing of the notice of allowance and be included in the PTA determination in the issue notification letter.	Number
  nonOverlappingDayQuantity	Patent term adjustment non overlapping days quantity number of overall summation of the USPTO delays minus any overlapping days.	Number
patentTermAdjustmentHistoryDataBag	The recordation of patent case actions that are involved in the patent term adjustment calculation.	N/A
  eventDescriptionText	A text field that denotes the use or function of the activity.	String
  eventSequenceNumber	The sequence in which the actions for a patent case are to be displayed.	Number
  originatingEventSequenceNumber	The sequence of the patent case action that started the time period for the Patent Case Action/Extension.	Number
  ptaPTECode	PTA or PTE code	String
  eventDate	The date of the legal status change event.	Date



Address and Attorney/Agent Information
Was this page helpful?
The Address and Attorney/Agent Information section provides additional information concerning the attorney/agent related to a patent, including the associated attorney/agent's address. Use this endpoint when you want address and attorney/agent information related to a specific patent application whose application number you know. You can test APIs right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/attorney

Returns attorney/agent data for supplied application number.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
recordAttorney	Details of the attorney or agent associated with an application/patent.	N/A
  customerNumberCorrespondenceData	Customer number	N/A
  patronIdentifier	Patron identifier	Number
  organizationStandardName	Organization standard name	String
powerOfAttorneyAddressBag	Collection of power of attorney address	N/A
  nameLineOneText	First line of name associated with attorney/agent correspondence address.	String
  nameLineTwoText	Second line of name associated with attorney/agent correspondence address.	String
  addressLineOneText	First line of address associated with attorney/agent correspondence address.	String
  addressLineTwoText	Second line of address associated with attorney/agent correspondence address.	String
  geographicRegionName	Geographic region name, e.g., state or province.	String
  geographicRegionCode	Geographic region code.	String
  postalCode	Postal code.	String
  cityName	City name.	String
  countryCode	Country code.	String
  countryName	Country name.	String
telecommunicationAddressBag	List of telecommunication addresses, such as the phone number(s) associated with the aforementioned attorney or agent.	N/A
  telecommunicationNumber	Telecommunication number, such as the phone number associated with the aforementioned attorney or agent.	String
  extensionNumber	Telecommunication extension	String
  telecomTypeCode	Telecommunication type code e.g: PHONE, FAX	String
powerOfAttorneyBag	Collection of power of attorney data	N/A
  nameLineOneText	First line of name associated with attorney/agent correspondence address.	String
  nameLineTwoText	Second line of name associated with attorney/agent correspondence address.	String
powerOfAttorneyBag	Power of attorney address data	N/A
  firstName	First name	String
  middleName	Middle name	String
  lastName	Last name	String
  namePrefix	Name prefix	String
  nameSuffix	Name suffix	String
  preferredName	Preferred name	String
  countryCode	Country code	String
  registrationNumber	Registration number	String
  activeIndicator	Active indicator	String
  registeredPractitionerCategory	Practitioner category	String
attorneyAddressBag	Attorney address bag	String
  nameLineOneText	First line of name associated with attorney/agent correspondence address.	String
  nameLineTwoText	Second line of name associated with attorney/agent correspondence address.	String
  addressLineOneText	First line of address associated with attorney/agent correspondence address.	String
  addressLineTwoText	Second line of address associated with attorney/agent correspondence address.	String
  geographicRegionName	Geographic region name, e.g., state or province.	String
  geographicRegionCode	Geographic region code.	String
  postalCode	Postal code.	String
  cityName	City name.	String
  countryCode	Country code.	String
  countryName	Country name.	String
telecommunicationAddressBag	List of telecommunication addresses, such as the phone number(s) associated with the aforementioned attorney or agent.	N/A
  telecommunicationNumber	Telecommunication number	String
  extensionNumber	Telecommunication extension	String
  telecomTypeCode	Telecommunication type code e.g: PHONE, FAX	String
attorneyBag	Power of attorney address data	N/A
  firstName	First name	String
  middleName	Middle name	String
  lastName	Last name	String
  namePrefix	Name prefix	String
  nameSuffix	Name suffix	String
  registrationNumber	Registration number	String
  activeIndicator	Active indicator	String
  registeredPractitionerCategory	Practitioner category	String
attorneyAddressBag	All the elements of the address that is on file for the attorney or agent associated with the application.	String
  nameLineOneText	First line of name associated with attorney/agent correspondence address.	String
  nameLineTwoText	Second line of name associated with attorney/agent correspondence address.	String
  addressLineOneText	First line of address associated with attorney/agent correspondence address.	String
  addressLineTwoText	Second line of address associated with attorney/agent correspondence address.	String
  geographicRegionName	Geographic region name, e.g., state or province.	String
  geographicRegionCode	Geographic region code.	String
  postalCode	Postal code.	String
  cityName	City name.	String
  countryCode	Country code.	String
  countryName	Country name.	String
telecommunicationAddressBag	List of telecommunication addresses, such as the phone number(s) associated with the aforementioned attorney or agent.	N/A
  telecommunicationNumber	Telecommunication number	String
  extensionNumber	Telecommunication extension	String
  telecomTypeCode	Telecommunication type code e.g: PHONE, FAX	String


Assignments
Was this page helpful?
The Assignments section provides additional information concerning the assignments of each patent. Use this endpoint when you want assignments data related to a specific patent application whose application number you know. You can test the API right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/assignment

Returns assignment data for supplied application number.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
assignmentBag	The collection of national assignments related to a patent or trademark.	N/A
  assignmentReceivedDate	The date an assignment was received. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
  reelNumber	1-6 digit number identifies the reel number to be used to locate the assignment on microfilm.	Number
  frameNumber	1-4 digit number that identifies the frame number to be used to locate the first image (page) of the assignment on microfilm.	Number
  reelAndFrameNumber	1-6 digit number identifies the reel number to be used to locate the assignment on microfilm. / 1-4 digit number that identifies the frame number to be used to locate the first image (page) of the assignment on microfilm.	String
  pageTotalQuantity	The total number of pages comprising the document	Number
  assignmentDocumentLocationURI	The Document Location URI	String
  assignmentRecordedDate	Identifies when the assignment was recorded in the USPTO. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
  conveyanceText	Contains textual description of the interest conveyed or transaction recorded.	String
  imageAvailableStatusCode	code to indicate the availability of the image	boolean
  assignmentMailedDate	The date an assignment request was mailed to the office or received by the office. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
assignorBag	Collection of assignors/details related to the assignor(s).	N/A
  executionDate	Identifies the date from the supporting legal documentation that the assignment was executed. Contains a date element with an 8-digit date in YYYY-MM-DD date format.	Date
  assignorName	A party that transfers its interest and right to the patent to the transferee (assignee) or the party receiving the patent.	String
assigneeBag	Collection of assignees/details related to the assignee(s).	N/A
  assigneeNameText	A person or entity that has the property rights to the patent, as a result of being the recipient of a transfer of a patent application or patent grant. Refers to ST.9 INID Code 73.	String
  assigneeAddress	Address details on file for the assignee.	N/A
  addressLineOneText	First line of address associated with the assignee.	String
  addressLineTwoText	Second line of address associated with the assignee.	String
  addressLineThreeText	Third line of address associated with the assignee.	String
  addressLineFourText	Fourth line of address associated with the assignee.	String
  cityName	Name of the city	String
  countryOrStateCode	Country or state code	String
  ictStateCode	International code for the state/region of the assignee (USPTO format)	String
  ictCountryCode	International code for the country of the assignee (USPTO format)	String
  geographicRegionName	Geographic region name	String
  geographicRegionCode	Geographic region code	String
  countryName	Country name.	String
  postalCode	Postal code	String
correspondenceAddress	The address of the patent correspondence	N/A
  correspondentNameText	The correspondent name	String
  addressLineOneText	First line of address associated with the correspondent.	String
  addressLineTwoText	Second line of address associated with the correspondent.	String
  addressLineThreeText	Third line of address associated with the correspondent.	String
  addressLineFourText	Fourth line of address associated with the correspondent, if applicable.	String
domesticRepresentative	The address of the domestic representative	N/A
  name	The domestic representative name.	String
  addressLineOneText	First line of address associated with the correspondent.	String
  addressLineTwoText	Second line of address associated with the correspondent.	String
  addressLineThreeText	Third line of address associated with the correspondent.	String
  addressLineFourText	Fourth line of address associated with the correspondent, if applicable.	String
  cityName	Name of the city	String
  postalCode	Postal code	String
  geographicRegionName	Geographic region name	String
  countryName	Country name.	String
  emailAddress	Email address of the representative.	Date


Foreign Priority
Was this page helpful?
The Foreign Priority section provides additional information concerning the foreign priority related to each patent. Use this endpoint when you want foreign priority information related to a specific patent application whose application number you know. You can test APIs right away in Swagger UI swagger icon.

This dataset includes published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/foreign-priority

Returns foreign priority data for supplied application number.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
foreignPriorityBag	Contains information about relevant foreign priority.	N/A
  filingDate	The date on which a priority claim was filed.	Date
  applicationNumberText	Free format of application number.	String
  ipOfficeName	Names of states, other entities and intergovernmental organizations the legislation of which provides for the protection of IP rights or which organizations are acting in the framework of a treaty in the field of IP	String



Associated Documents
Was this page helpful?
The Associated Documents section contains the PGPUB XML extracted from the bulk data product "Patent Application Full-Text Data (No Images)" zip file. It also includes the Patent Grant XML extracted from the bulk data product "Patent Grant Full-Text Data (No Images) - XML" zip file if the corresponding application has PGPUB/Patent Grant data available. You can test the API right away in Swagger UI swagger icon.

These XML datasets are only available for published patent applications and issued patent data filed after January 1, 2001. This data is refreshed daily.

GET https://api.uspto.gov/api/v1/patent/applications/{applicationNumberText}/associated-documents

e.g. https://api.uspto.gov/api/v1/patent/applications/16330077/associated-documents

Returns Associated Documents for supplied application number.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
PatentFileWrapperDataBag	Patent File Wrapper data.	N/A
  applicationNumberText	The unique number assigned by the USPTO to a patent application when it is filed.	String
grantDocumentMetaData	Grant document meta data.	N/A
  productIdentifier	Product identifier.	String
  zipFileName	Zip file name	String
  fileCreateDateTime	The date file was created.	Date
  xmlFileName	XML file name.	String
  fileLocationURI	File location URI.	String
pgpubDocumentMetaData	Details of PgPub document meta data.	N/A
  productIdentifier	Product identifier.	String
  zipFileName	Zip file name	String
  fileCreateDateTime	The date file was created.	Date
  xmlFileName	XML file name.	String
  fileLocationURI	File location URI.	String


Status Codes
Was this page helpful?
Conduct a search of all patent status codes and description Use this endpoint if you are interested in fetching/searching patents status codes or status code description. For example, you want to return all patents status code description that match your search term, such as Rejection or Abandonment. You can also use multiple search terms, such as “Payment AND Received” .

Other details for using the Search endpoint:

If you don’t specify the field in which you want us to look for this search term, we will look for it across all data fields () and return any matching status codes and corresponding description.
All search syntaxes are applicable to this endpoint, meaning any number of combinations is possible. Some example requests are below, but for more information, view the Simplified Syntax documentation that is linked in the Open Data Portal API page. You can also test the API right away in Swagger UI swagger icon.

GET https://api.uspto.gov/api/v1/patent/status-codes

Returns a list of all patents status codes and its corresponding description.

Note: API Key is required. Obtain an API key.

POST See Swagger documentation

Returns a list of all patents and applications that match your search term.

Note: API Key is required. Obtain an API key.

If you have any questions or errors, please visit the Support page for assistance.

Response
Successful request.

Data Property	Description	Type
statusCodeBag	Status code bag.	N/A
  applicationStatusCode	Status codes.	Number
  applicationStatusDescriptionText	Application status code description.	String
