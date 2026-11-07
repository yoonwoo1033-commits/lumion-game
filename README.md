# LUMION — 루미온 v1

오리지널 루미온 20종의 이미지, 4개 지역, 탐험, 전투, 포획, 도감, 상점, 경험치 사탕, 진화, 기술 배치, 수면 기록을 포함하는 Streamlit 게임입니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub 및 Streamlit 배포

`lumion-game` 저장소의 `lumion_standalone` 폴더에 **이 패키지 안의 파일과 assets 폴더를 모두** 업로드하세요.
Streamlit Community Cloud의 **Main file path**는 `lumion_standalone/app.py`로 설정하세요.
이전 `lumion_standalone/app.py`와 `engine.py`는 새 버전으로 교체하고, `assets` 하위 폴더를 그대로 유지하세요.

## 현재 버전의 제한

- 캐릭터는 이미지가 준비된 20종입니다. 100종과 오로라 전용 이미지는 아직 없습니다. 오로라 확률 1/500은 적용되지만 현재는 같은 캐릭터 그림에 표지만 붙습니다.
- 캐릭터 등장에 CSS 페이드 애니메이션을 적용했습니다. 24프레임 스프라이트 애니메이션은 아직 없습니다.
- 로그인·Supabase 저장은 미구현입니다. 세션 상태는 새로고침/서버 재시작 시 초기화될 수 있으니 설정에서 JSON으로 백업하세요.
- 전투는 HP·기술 위력·명중률·속성 상성·레벨을 적용하는 간소화된 턴제 시스템입니다. 상태이상 및 고급 AI는 아직 없습니다.
- 수면 지표는 직접 입력하며 실제 수면 측정 기능이 아닙니다. PVT는 평균값 수동 기록입니다.
- 개발용 코인 10,000개 지급은 테스트 전용입니다.
- 이 프로젝트는 원래 포켓몬 저장소를 변경하지 않습니다.
