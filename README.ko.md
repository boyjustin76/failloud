# failloud

**데스크톱 자동화는 조용히 실패한다. 이 라이브러리는 그걸 시끄럽게 만든다.**

여기 들어 있는 함정은 전부 **그때는 성공처럼 보였던 것**들입니다.

- 프레임 추출기가 `142장 뽑음` 이라고 찍었습니다. 디스크에는 한 장도 없었습니다.
- 실패한 작업을 찍었더니 시작 화면이 나왔습니다. 진짜 원인인 작은 대화상자는 그 옆에 있었고, 안 찍혔습니다.
- `D:/exports ` 로 내보냈더니 그 안에 쓰는 파일마다 `FileNotFoundError` 가 났습니다.
  그런데 `os.path.exists("D:/exports ")` 는 계속 `True` 를 돌려줬습니다.
- 자동화가 5분 만에 시간 초과로 끝났습니다. 앱은 그동안 모달 대화상자 앞에 멈춰 있었고,
  그게 무슨 창이었는지 아무도 말할 수 없었습니다.

넷 다 **예외를 내지 않았습니다.** `failloud` 는 이것들을 오류로 바꾸는 장치 모음입니다.

```bash
pip install git+https://github.com/boyjustin76/failloud          # 핵심 장치, 의존성 없음
pip install "failloud[capture] @ git+https://github.com/boyjustin76/failloud"  # + 창 찍기
```

> 아직 PyPI 에 없습니다. 첫 태그 배포 전까지는 저장소에서 바로 설치합니다.

## 들은 말 말고, 쓴 것을 세어 본다

```python
from failloud.fs import write_bytes_checked, expect_file_count

for index, frame in enumerate(frames):
    write_bytes_checked(out_dir / f"{index:05d}.png", encode(frame))

expect_file_count(out_dir, "*.png", len(frames))   # 쓴 것이 거짓이면 여기서 터진다
```

`cv2.imwrite()` 는 윈도에서 한글 경로에 못 씁니다. 예외를 내지 않고 **`False` 만** 돌려줍니다.
메모리에서 인코딩하고 바이트는 파이썬이 쓴 다음, 수를 세어 대조하면 됩니다.

## 자동화를 멈춰 세운 대화상자를 읽는다

```python
from failloud.windows import find_modal, capture_window

modal = find_modal("Illustrator")
if modal:
    print(modal.message)      # "스크립트 경고  확인  그림을 저장할 수 없습니다."
    capture_window("fail.png", hwnd=modal.window.hwnd)
```

COM·스크립트 호출은 앱이 대화상자를 띄우는 순간 거기서 멈춥니다 — 반환값도 예외도 없습니다.
**죽이기 전에** 읽어야 합니다.

"어도비 대화상자는 속을 못 읽는다" 는 말이 돌지만, 그건 UI Automation 이야기입니다.
Win32 `EnumChildWindows` 로는 제목도 본문도 그대로 나옵니다.

## 화면에 없는 창도 찍는다

```python
from failloud.windows import capture_window, capture_all

capture_window("app.png", proc="AfterFX")     # 가려져 있어도 찍힌다
capture_all("evidence/", proc="AfterFX")      # 원인을 모를 때는 창을 전부
```

`PrintWindow(PW_RENDERFULLCONTENT)` 는 창이 스스로 그리게 합니다. 가려져 있어도, 다른 가상
데스크톱에 있어도 나오고, 포커스를 뺏지 않아 사람이 하던 일을 방해하지 않습니다.

창을 찾을 때 `Process.MainWindowHandle` 은 쓰지 마세요. 일러스트레이터는 거기서 **160x28**
짜리 엉뚱한 핸들을 돌려줍니다. 최상위 창을 훑어 가장 큰 것을 고르면 진짜 창(**1900x1012**)이 나옵니다.

## 경로를 박지 않는다

```python
from failloud.fs import find_ancestor_dir, safe_join

workspace = find_ancestor_dir(["lab/work", "work"], env_var="WORK_DIR")
target = safe_join(workspace, user_supplied_name, "output.png")
```

`safe_join` 은 **모든 조각**을 다듬습니다. 터지는 자리는 부모로 쓰이는 조각이기 때문입니다.

## 이 라이브러리가 하지 않는 것

**창을 닫지 않습니다.** 키 입력 흉내는 포커스가 가 있는 아무 창으로나 새어 들어가고, 좌표 클릭은
화면 크기·DPI·앞창 순서를 가정합니다. 한 번은 빗나간 클릭이 엉뚱한 앱을 띄웠습니다.
읽고 · 찍고 · 적고 · **사람에게 말합니다.**

## 범위

| 묶음 | 플랫폼 | 의존성 |
|---|---|---|
| `failloud.fs` | 어디나 | 없음 |
| `failloud.windows` | 윈도 | Pillow |

`failloud.windows` 는 다른 OS 에서 **왜 안 되는지 말하는 `ImportError`** 를 냅니다.
덕분에 파일 쪽 장치는 어디서나 그대로 쓸 수 있습니다.

자세한 측정값은 [`docs/traps.md`](docs/traps.md), 영어 설명은 [README.md](README.md).

MIT 라이선스.
