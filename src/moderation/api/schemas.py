from __future__ import annotations          # 아직 만들어지지 않은 타입도 참조할 수 있도록(인터프리터 언어 특성상 순서대로 작성되어야만 인식할 수 있지만 이 문제를 해결해주는 라이브러리)

from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

#### ENUM, 타입 등을 지정하는 파일

### ENUM  정의

# 판단 결과
class Verdict(StrEnum):         # String 타입의 Enum을 사용할 때는 이걸 사용
    ALLOW = "ALLOW"
    FLAG = "FLAG"
    BLOCK = "BLOCK"

# 수치
class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

# 카테고리
class Category(StrEnum):
    PROFANITY = "PROFANITY"             # 욕설, 비속어
    HATE="HATE"                         # 혐오, 차별
    HARASSMENT="HARASSMENT"             # 특정 대상에 대한 괴롭힘, 비방
    SEXUAL="SEXUAL"                     # 성적 유해
    VIOLENCE="VIOLENCE"                 # 폭력, 위협
    SPAM="SPAM"                         # 광고, 도배, 피싱
    PII="PII"                           # 개인정보 노출
    SELF_HARM="SELF_HARM"               # 자해
    ILLEGAL="ILLEGAL"                   # 불법 거래, 약물
    CONTROVERSIAL="CONTROVERSIAL"       # 정치, 종교, 사회적 논쟁 주제
    OTHER="OTHER"                       # 기타


### 타입 정의

# 대상 유형
class Content(BaseModel):
    model_config = ConfigDict(extra="forbid")               # 알 수 없는 타입이 넘어오면 Error를 반환

    type: Literal["text"] = "text"                          # 지원하고자 하는 타입. text 타입을 허용함
    text: str = Field( min_length=1, max_length=10000 )     # 해당 타입으로 넘어온 결과는 반드시 Field() 괄호 내 조건을 만족해야 함

# 정책
class Mode(StrEnum):
    FULL = "full"
    RULES_ONLY = "rules_only"

class Options(BaseModel):
    model_config = ConfigDict(extra="ignore")           # ignore: 조용히 무시하기 / forbid: 에러로 반환하기

    policy: str = Field( default="default", min_length=1, max_length=100 )  # 정책명
    mode: Mode = Mode.FULL          # = 값  을 통해 기본 값을 지정할 수 있음
    explain: bool = True            # bool은 기본 값만 지정해주면 됨( Field가 필요 없음 )

# 대상 구분
class Surface(StrEnum):
    POST="post"
    COMMENT="comment"
    DM="dm"
    NICKNAME="nickname"
    PROFILE="profile"
    OTHER="other"

class Context(BaseModel):
    model_config = ConfigDict(extra="ignore")

    content_id: str | None = Field( default=None, min_length=1, max_length=100 )        # |을 통해 둘 중 하나로 타입을 만들 수 있음, nullable 설정시 필요
    author_id: str | None = Field( default=None, min_length=1, max_length=100 )
    surface: Surface | None = None
    locale: str = Field( default="ko", min_length=1, max_length=15 )           # 추후 ENUM으로 변경
    parent_id: str | None = Field( default=None, min_length=1, max_length=100 )

### Request DTO 정의
## Python에서 클래스 초기화는 최초 실행시 한 번만 이루어지게 됨
## 그렇기 때문에 같은 클래스(타입)의 객체를 여러개 만들어도 같은 것으로 취급됨.
## 아 문제를 해결해주는 것이 default_factory
class ModerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Content
    context: Context = Field( default_factory=Context ) # 각 요청마다 새로 객체를 생성하게 지정
    options: Options = Field( default_factory=Options ) # 여기에 Options()라고 하면 이후 이 타입을 쓰는 모든 객체가 Options을 공유하게 됨

### Response DTO 정의
# 위반된 결과
class Label(BaseModel):
    category: Category
    severity: Severity
    score: float = Field( ge=0.0, le=1.0 )      # 숫자용 범위 조건. ge: 이상 / gt: 초과 / le: 이하 / lt: 미만

# 위반한 정책
class MatchedRule(BaseModel):
    rule_id: str
    matched: str
    position: tuple[int, int]   # list[int]는 인자가 0개 이상이 될 수 있는 반면 tuple은 2개로 고정할 수 있기 때문에 사용(어차피 파싱되면 배열)

# TODO: RAG+LangChain 기능 붙이면 사용할 스키마
class Guideline(BaseModel):
    id: str
    title: str
    excerpt: str
    score: float

# 정책 위반 사유
class Explanation(BaseModel):
    matched_rule: list[MatchedRule] = Field( default_factory=list )
    llm_reason: str | None = None
    guidelines: list[Guideline] = Field( default_factory=list )

# 메타데이터
class Meta(BaseModel):
    request_id: str
    policy: str = "default"
    stages: list[str] = Field( default_factory=list )
    latency_ms: int
    degraded: bool = False
    degraded_reason: str | None = None

# 최종 모더레이션 결과
class DecidedBy(StrEnum):
    RULE = "RULE"
    LLM = "LLM"
    RULE_LLM = "RULE_LLM"
    FALLBACK = "FALLBACK"

class ModerationResult(BaseModel):
    verdict: Verdict                # 결과 ALLOW / FLAG / BLOCK
    allowed: bool                   # ALLOW는 true, FLAG는 일단 true이긴 한데 확인 필요, BLOCK은 false
    confidence: float          # 해당 문제에 대한 판단 점수? 확률? 포인트?
    labels: list[Label] = Field( default_factory=list ) # 위반된 결과. 없으면 빈 배열
    decided_by = DecidedBy          # 어떤 필터에 의해 결정되었는지
    explanation: Explanation | None = None  # 평가 사유
    meta: Meta                      # 메타데이터