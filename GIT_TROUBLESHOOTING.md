# Git 파일 스테이징 문제 해결 가이드

## 문제 증상
- `git add` 후에도 파일이 staged 상태가 되지 않음
- `git status`에서 계속 "커밋하도록 정하지 않은 변경 사항"으로 표시됨

## 해결 방법 (순서대로 시도)

### 1. Extended Attributes 제거 (macOS)
```bash
xattr -c [파일명]
git add [파일명]
```

### 2. Git 인덱스 새로고침
```bash
git update-index --refresh --ignore-submodules
git add [파일명]
```

### 3. assume-unchanged 플래그 확인/해제
```bash
git update-index --no-assume-unchanged [파일명]
git add [파일명]
```

### 4. 파일 완전 재생성
```bash
mv [파일명] [파일명].backup
cp [파일명].backup [파일명]
rm [파일명].backup
git add [파일명]
```

### 5. Git 인덱스 완전 재구성 (최후 수단)
```bash
git rm --cached [파일명]
git add [파일명]
```

## 예방 방법

### macOS 사용자
```bash
# .gitconfig에 추가
git config --global core.precomposeunicode true
git config --global core.quotepath false
```

### 프로젝트별 설정
```bash
# 프로젝트 루트에 .gitattributes 파일 생성
echo "* text=auto" > .gitattributes
echo "*.md text" >> .gitattributes
```

## 디버깅 명령어
```bash
# 파일 상태 확인
git ls-files --stage [파일명]
git diff [파일명]
git diff --cached [파일명]

# Extended attributes 확인 (macOS)
ls -la [파일명]  # @ 표시 확인
xattr -l [파일명]  # 상세 attributes 확인
```