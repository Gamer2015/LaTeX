import os


result = '['
for line in open("resources/nutrients.txt", "r").read().splitlines():
	result += '	{' 
	result += '\n		\'apiName\': \'' + line + '\''
	result += '\n		\'label\': \'' + line + '\''
	result += '\n		\'default\': \'0.001\'\n	}, \n'
result += ']'

f = open("resources/parsedNutrients.txt","w")
f.write(result)
f.close()


"""<fields>
		<fullName>skDietThiaminSI__c</fullName>
		<externalId>false</externalId>
		<formula>skDietThiamin__c * VALUE(TEXT( skDietThiaminUnit__c ))</formula>
		<formulaTreatBlanksAs>BlankAsZero</formulaTreatBlanksAs>
		<label>• Vitamin B1 (Thiamin) SI</label>
		<precision>18</precision>
		<required>false</required>
		<scale>18</scale>
		<trackTrending>false</trackTrending>
		<type>Number</type>
		<unique>false</unique>
	</fields>
	<fields>
		<fullName>skDietThiaminUnit__c</fullName>
		<defaultValue>&apos;0.000000001&apos;</defaultValue>
		<externalId>false</externalId>
		<label>• Vitamin B1 (Thiamin) Unit</label>
		<required>false</required>
		<trackTrending>false</trackTrending>
		<type>Picklist</type>
		<valueSet>
			<restricted>true</restricted>
			<valueSetName>skSIMass</valueSetName>
		</valueSet>
	</fields>
	<fields>
		<fullName>skDietThiamin__c</fullName>
		<externalId>false</externalId>
		<label>• Vitamin B1 (Thiamin)</label>
		<precision>18</precision>
		<required>false</required>
		<scale>2</scale>
		<trackTrending>false</trackTrending>
		<type>Number</type>
		<unique>false</unique>
	</fields>"""
