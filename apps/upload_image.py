from google.cloud import storage
import uuid


# import os

storage_client = storage.Client()


def upload_image(bucket_name, path, file):
    """
    이미지를 주어진 버킷 이름에 업로드하고 다운로드할 수 있는 경로를 반환

    path는 폴더 이름 문자열인데 마지막을 /로 끝내야 함. (travel/)

    '버킷 이름/path/새로 만든 이미지명' 이런식으로 저장
    """

    # 버킷 선택
    bucket = storage_client.get_bucket(bucket_name)
    # 확장자만 복사 eg. "foo.bar.JPG" -> "jpg"
    ext = file.filename.rsplit('.', 1)[1].lower()

    # 이 이미지에 쓰일 새로운 파일이름 무작위 생성
    generated_filename = path + str(uuid.uuid4()) + '.' + ext

    # 새롭게 만든 파일명과 버킷 이름으로 경로 완성
    blob = bucket.blob(generated_filename)

    # 경로에 파일 실제로 쓰기
    blob.upload_from_file(file)

    # 아래 경로에 들어가면 방금 올린 이미지를 다운로드할 수 있음 (물론 버킷에의 접근 권한이 있을 때)
    return "https://storage.googleapis.com/" + bucket_name + '/' + generated_filename
