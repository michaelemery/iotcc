import mysql.connector

def getDbCursor():
    connection = mysql.connector.connect(user='iotcc_user',password='158335danish',host='iotcc-db-instance.cqmmjgzwow7o.us-west-2.rds.amazonaws.com',database='microhort')
    cursor = connection.cursor()
    return connection, cursor
    
def cleanUpDb(connection, cursor):
    cursor.close()
    connection.close()