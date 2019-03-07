import json
from pprint import pprint

arr = 0
with open('resources/nutrientData.json') as f:
    arr = json.load(f)

resultString = ''
for obj in arr:
	resultString += """
	<fields> 
        <fullName>skDiet""" + obj['apiName'] + """SI__c</fullName> 
        <externalId>false</externalId> 
        <formula>skDiet""" + obj['apiName'] + """__c * VALUE(TEXT( skDiet""" + obj['apiName'] + """Unit__c ))</formula> 
        <formulaTreatBlanksAs>BlankAsZero</formulaTreatBlanksAs> 
        <label>• """ + obj['label'] + """ SI</label> 
        <precision>18</precision> 
        <required>false</required> 
        <scale>18</scale> 
        <trackTrending>false</trackTrending> 
        <type>Number</type> 
        <unique>false</unique> 
    </fields> 
    <fields> 
        <fullName>skDiet""" + obj['apiName'] + """Unit__c</fullName> 
        <defaultValue>&apos;""" + obj['default'] + """&apos;</defaultValue> 
        <externalId>false</externalId> 
        <label>• """ + obj['label'] + """ Unit</label> 
        <required>false</required> 
        <trackTrending>false</trackTrending> 
        <type>Picklist</type> 
        <valueSet> 
            <restricted>true</restricted> 
            <valueSetName>skSIMass</valueSetName> 
        </valueSet> 
    </fields> 
    <fields> 
        <fullName>skDiet""" + obj['apiName'] + """__c</fullName> 
        <externalId>false</externalId> 
        <label>• """ + obj['label'] + """</label> 
        <precision>18</precision> 
        <required>false</required> 
        <scale>2</scale> 
        <trackTrending>false</trackTrending> 
        <type>Number</type> 
        <unique>false</unique> 
    </fields>"""


f = open("resources/fieldString.txt","w")
f.write(resultString)
f.close()
