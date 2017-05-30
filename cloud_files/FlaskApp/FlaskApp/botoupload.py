import boto3

def uploadFileToMicroHortS3(file, filename):

    ACCESS_KEY = 'SEECLIFFFORKEY'
    SECRET_KEY = 'SEECLIFFFORKEY'

    client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )

    response = client.put_object(Body = file, Key =("pictures/" + filename), Bucket = "microhort")
