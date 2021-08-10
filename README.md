# STEP 3(코드리뷰)

-   STEP2에 완성된 부분을 Django Ninja로 변경 해보자
    -   제약 조건
        -   poetry 사용
        -   rule 추가
            -   branch
            -   commit
            -   PR(prlint)
        -   pre-commit 사용
            -   black
            -   isort
            -   mypy
            -   flake8
        -   github actions
        -   티켓 생성
            -   description 작성
                -   문제
                -   해결
                -   조건
                -   절차
                -   테스트
        -   PR 생성 → 코드리뷰 → 개인 main branch에 merge flow로 진행
-   결과물
    -   feature 별 티켓
    -   Post
        -   CRUD
    -   Comment
        -   CRUD
    -   Auth with JWT
    -   각 API에 대한 Swagger 문서

------



# STEP3 참고사항

## 개발 환경 구축을 해보자

### 설치 라이브러리

1.  pyenv
2.  pyenv-virtualenv



### 파이썬

-   버젼
    -   3.9.4
-   가상환경명
    -   dj_girls_final

### 장고

-   최신 버젼



### 파이참 설정

-   project interpreter 설정
-   project structure 설정

1.  어떤 도구인가?
2.  이것을 사용하는 목적은 무엇인가?
3.  어떻게 사용하는 것인가?
    1.  사용방법을 간단하게 기술
4.  기타 등등 → 추가로 적을게 있다면 적어도 됨



### 항목들

-   flake8
-   black
-   mypy
-   pydantic
-   pytest
-   poetry
-   ipdb
-   isort
-   pre-commit
-   freezegun
-   django-extensions
-   django-environ



# 규칙들

## Branch

1.  base branch: bcy-main or shk-main
2.  code-review branch: bcy-code-review or shk-code-review
3.  feature branch: prol-{티켓번호}-티켓에-대한-설명을-영어로
    1.  ex) prol-12-add-reset-password-validate-login-in-handle-reset-password-func

## Commit

1.  format: PROL-12 커밋에-대한-자세한-내용
2.  어떤 일을 했는지 자세히 드러나도록 적어주자(이유까지 나와있다면 베스트)
    1.  ex)
        1.  PROL-12 extract handling method for readability
        2.  PROL-150 add comment on test class for clarity
        3.  PROL-150 fix typo in test comment

## PR

1.  PR title format: PROL-12 blah blah blah
2.  PR Description format: 정해진 포맷은 없고, 티켓에 대한 간단한 설명 및 작업 내용 정도 적어주면 좋을 것 같다
    1.  FYI, 자세한 내용은 티켓에 명시해주자

## PR Life Cycle

1.  티켓 생성
2.  티켓 번호에 해당하는 로컬 branch 생성
3.  로컬 branch에서 코드 작업
4.  origin으로 로컬 branch push
5.  PR 생성 - merge branch를 {이니셜}-code-review branch로 설정
6.  코드 리뷰
7.  {이니셜}-code-review branch에 Merge
8.  {이니셜}-main branch에 origin/로컬 branch 명을 Merge
9.  origin/{이니셜}-main으로 Push
