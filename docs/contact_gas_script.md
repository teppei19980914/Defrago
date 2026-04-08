# お問い合わせ受信用 Google Apps Script

Defrago のお問い合わせ機能 (#4) は、フォーム送信を外部の Google Apps Script
(GAS) Web App に POST し、GAS 側で Google Sheets への記録と Gmail 通知を行う
構成になっている。本ドキュメントは、その GAS スクリプトの実装と設定手順を
まとめる。

## 全体像

```
ユーザー
  │ POST /api/iconbar/contact/submit (フォーム)
  ▼
Defrago (FastAPI)
  │ 入力検証 → httpx で POST (JSON, Content-Type: text/plain)
  ▼
GAS Web App (doPost)
  │ ① Google Sheets に行追加
  │ ② 開発者に Gmail で通知
  ▼
Defrago へ JSON レスポンス返却 → ユーザーに「送信完了」表示
```

Defrago が送る JSON ペイロードの形式:

```json
{
  "type": "inquiry_defrago",
  "category": "question | bug | feature | other",
  "email": "user@example.com",
  "text": "問い合わせ本文 (20〜2000 文字)",
  "user_key": "ユーザーUUID",
  "submitted_at": "2026-04-08T12:34:56+00:00"
}
```

## 1. セットアップ手順

### 1-1. Google Sheets を作成

1. https://sheets.google.com/ で新規スプレッドシートを作成
2. 名前を `Defrago Contact Inbox` 等に変更
3. 1 行目に以下のヘッダーを入力（**順序が重要**）:

   | A | B | C | D | E | F | G |
   |---|---|---|---|---|---|---|
   | 受信日時 | 種別 | メール | 本文 | user_key | 送信日時(クライアント) | 既読 |

4. 「既読」列 (G) は後で手動チェック用（返信済みフラグ）
5. ブラウザ URL の `/d/{SHEET_ID}/edit` 部分からスプレッドシート ID を控える

### 1-2. Apps Script プロジェクトを作成

1. スプレッドシート右上 **拡張機能** → **Apps Script**
2. 開いた Apps Script エディタのプロジェクト名を `Defrago Contact Receiver` に変更
3. デフォルトの `Code.gs` を削除し、本ドキュメント「2. スクリプト本体」の
   コードを丸ごと貼り付け

### 1-3. スクリプトプロパティを設定（機密情報）

Apps Script エディタ → 左メニュー **プロジェクトの設定** (歯車アイコン) →
**スクリプト プロパティ** → **スクリプト プロパティを追加** で以下の 2 件を設定:

| キー | 値 | 説明 |
|---|---|---|
| `SPREADSHEET_ID` | 1-1 で控えた ID | 記録先スプレッドシート |
| `NOTIFY_EMAIL` | 例: `you@example.com` | Gmail 通知の宛先 |

### 1-4. Web App としてデプロイ

1. Apps Script エディタ右上 **デプロイ** → **新しいデプロイ**
2. **種類の選択** (歯車) → **ウェブアプリ**
3. 設定:
   - **説明**: `Defrago Contact v1`
   - **次のユーザーとして実行**: **自分** (`your-google-account@gmail.com`)
   - **アクセスできるユーザー**: **全員** (Defrago からは匿名で POST される
     ため必須)
4. **デプロイ** をクリック
5. 初回は認可ダイアログが開く → Google アカウントを選択 →
   「詳細」→「(プロジェクト名) に移動 (安全ではないページ)」→ **許可**
   (自作スクリプトなので問題なし)
6. 発行された **ウェブアプリの URL** (`https://script.google.com/macros/s/XXXX/exec`)
   をコピー

### 1-5. Render に環境変数を設定

1. Render ダッシュボード → `defrago` → **Environment**
2. **Add Environment Variable**:
   - Key: `CONTACT_WEBHOOK_URL`
   - Value: 1-4 で発行された Web App URL
3. **Save Changes** → 自動再デプロイ

## 2. スクリプト本体

以下を Apps Script の `Code.gs` に貼り付ける。

```javascript
/**
 * Defrago お問い合わせ受信用 Google Apps Script
 *
 * Defrago (FastAPI) から POST される JSON を受け取り、
 * Google Sheets に記録し Gmail で開発者に通知する。
 *
 * セットアップ:
 *   1. スクリプトプロパティに SPREADSHEET_ID と NOTIFY_EMAIL を設定
 *   2. Web App としてデプロイ (実行: 自分, アクセス: 全員)
 *   3. 発行された URL を Render の CONTACT_WEBHOOK_URL に設定
 */

// ---------- 定数 ----------

/** Defrago の category 値と日本語ラベルの対応。 */
const CATEGORY_LABELS = {
  question: '質問',
  bug: '不具合報告',
  feature: '機能要望',
  other: 'その他',
};

/** 想定する type 値。想定外の type はリクエストを拒否する。 */
const EXPECTED_TYPE = 'inquiry_defrago';

/** テキスト本文の最小/最大長 (Defrago 側のバリデーションと揃える)。 */
const MIN_TEXT_LENGTH = 20;
const MAX_TEXT_LENGTH = 2000;

/** メールアドレス簡易バリデーション用の正規表現。 */
const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

// ---------- メインハンドラ ----------

/**
 * POST リクエストを受信する。
 *
 * @param {GoogleAppsScript.Events.DoPost} e
 * @return {GoogleAppsScript.Content.TextOutput}
 */
function doPost(e) {
  try {
    const payload = parsePayload(e);
    validatePayload(payload);

    appendToSheet(payload);
    sendNotificationEmail(payload);

    return jsonResponse({ ok: true });
  } catch (err) {
    console.error('doPost failed: ' + err + '\n' + err.stack);
    return jsonResponse({ ok: false, error: String(err.message || err) }, 400);
  }
}

/**
 * GET リクエスト (ヘルスチェック用)。
 *
 * Defrago からは使われないが、ブラウザで URL にアクセスして
 * 動作確認できるようにしておく。
 */
function doGet() {
  return jsonResponse({ ok: true, service: 'defrago-contact' });
}

// ---------- 詳細ロジック ----------

/**
 * リクエストボディを JSON として解釈する。
 *
 * Defrago は Content-Type: text/plain で JSON を送ってくるため
 * e.postData.contents を直接 JSON.parse する。
 */
function parsePayload(e) {
  if (!e || !e.postData || !e.postData.contents) {
    throw new Error('empty request body');
  }
  try {
    return JSON.parse(e.postData.contents);
  } catch (parseErr) {
    throw new Error('invalid JSON: ' + parseErr.message);
  }
}

/**
 * ペイロードの妥当性を検査する。
 *
 * 本来のバリデーションは Defrago 側でも行われているが、
 * Web App は公開されており第三者からも叩けるため、GAS 側でも
 * 最低限の検証を行いスプレッドシート汚染を防ぐ。
 */
function validatePayload(p) {
  if (!p || typeof p !== 'object') {
    throw new Error('payload is not an object');
  }
  if (p.type !== EXPECTED_TYPE) {
    throw new Error('unexpected type: ' + p.type);
  }
  if (!CATEGORY_LABELS[p.category]) {
    throw new Error('invalid category: ' + p.category);
  }
  if (typeof p.email !== 'string' || !EMAIL_REGEX.test(p.email) || p.email.length > 254) {
    throw new Error('invalid email');
  }
  if (
    typeof p.text !== 'string' ||
    p.text.length < MIN_TEXT_LENGTH ||
    p.text.length > MAX_TEXT_LENGTH
  ) {
    throw new Error('invalid text length');
  }
  // user_key / submitted_at は任意 (将来の拡張に備え緩めに)
}

/**
 * スプレッドシートに 1 行追加する。
 *
 * 列順: 受信日時 / 種別 / メール / 本文 / user_key / 送信日時 / 既読
 */
function appendToSheet(p) {
  const spreadsheetId = getRequiredProperty('SPREADSHEET_ID');
  const sheet = SpreadsheetApp.openById(spreadsheetId).getSheets()[0];
  sheet.appendRow([
    new Date(), // A: 受信日時 (GAS 側)
    CATEGORY_LABELS[p.category] || p.category, // B: 種別 (日本語ラベル)
    p.email, // C: メール
    p.text, // D: 本文
    p.user_key || '', // E: user_key
    p.submitted_at || '', // F: 送信日時 (クライアント側)
    false, // G: 既読フラグ (初期値 false)
  ]);
}

/**
 * 開発者に Gmail 通知を送信する。
 *
 * Gmail の 1 日あたり送信上限 (通常 100 通/日) に注意。
 * 大量のスパムが来る場合はここで抑制ロジックを検討する。
 */
function sendNotificationEmail(p) {
  const to = getRequiredProperty('NOTIFY_EMAIL');
  const categoryLabel = CATEGORY_LABELS[p.category] || p.category;

  const subject = '[Defrago] 新しいお問い合わせ (' + categoryLabel + ')';
  const body = [
    'Defrago に新しいお問い合わせが届きました。',
    '',
    '■ 種別: ' + categoryLabel,
    '■ メール: ' + p.email,
    '■ user_key: ' + (p.user_key || '(不明)'),
    '■ 送信日時: ' + (p.submitted_at || '(不明)'),
    '',
    '--- 本文 ---',
    p.text,
    '--- 本文ここまで ---',
    '',
    'スプレッドシートで全件を確認: ' +
      'https://docs.google.com/spreadsheets/d/' +
      getRequiredProperty('SPREADSHEET_ID'),
  ].join('\n');

  MailApp.sendEmail({
    to: to,
    subject: subject,
    body: body,
    // 返信先をユーザーのメールアドレスに設定しておくと、
    // Gmail で「返信」を押しただけで直接ユーザーへ返信できる。
    replyTo: p.email,
  });
}

// ---------- ユーティリティ ----------

/**
 * スクリプトプロパティから値を取得する。未設定ならエラー。
 */
function getRequiredProperty(key) {
  const value = PropertiesService.getScriptProperties().getProperty(key);
  if (!value) {
    throw new Error('Script property missing: ' + key);
  }
  return value;
}

/**
 * JSON レスポンスを返す。
 *
 * ContentService は HTTP ステータスコードを直接制御できないため、
 * エラー時でも 200 を返し、ボディの ok=false で判別する。
 */
function jsonResponse(obj, _unusedStatus) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
```

## 3. 動作確認

### 3-1. GAS エディタ上での単体テスト

Apps Script エディタで以下のテスト関数を実行し、スプレッドシートに
ダミー行が追加されるか確認する (初回は認可ダイアログが出る)。

```javascript
/**
 * 手動実行用のテスト関数。
 *
 * Apps Script エディタで関数選択に「_manualTest」を選び実行ボタンを押す。
 */
function _manualTest() {
  const fakeEvent = {
    postData: {
      contents: JSON.stringify({
        type: 'inquiry_defrago',
        category: 'question',
        email: 'test@example.com',
        text: 'これは手動テスト用の問い合わせ本文です。ダミーデータ。',
        user_key: 'test-user-id',
        submitted_at: new Date().toISOString(),
      }),
    },
  };
  const response = doPost(fakeEvent);
  console.log(response.getContent());
}
```

期待される動作:

- Apps Script の実行ログに `{"ok":true}` が表示される
- スプレッドシートに 1 行追加される
- `NOTIFY_EMAIL` にメールが届く

### 3-2. Defrago 経由のエンドツーエンドテスト

1. Render に `CONTACT_WEBHOOK_URL` を設定して再デプロイ済みであることを確認
2. `https://defrago.onrender.com/` にログイン
3. アイコンバーの **お問い合わせ** アイコンをクリック
4. フォームに以下を入力して送信:
   - 種別: 質問
   - メール: 自分のテストアドレス
   - 内容: 20 文字以上の適当な本文
5. 「お問い合わせを送信しました」が表示されれば成功
6. スプレッドシートと Gmail にも記録されていることを確認

## 4. 運用メモ

### 返信フロー

- Gmail に届いた通知メールで **返信** ボタンを押すと、`replyTo` が
  問い合わせ者のメールに設定されているため、そのまま返信できる
- 返信完了後、スプレッドシートの「既読」列 (G) を `TRUE` に手動更新すると
  追跡しやすい

### スパム対策

現状スクリプトに実装されている対策は以下のみ:

1. `type == 'inquiry_defrago'` チェック
2. email / text / category の形式バリデーション

もし大量スパムが来た場合、追加できる対策:

- **IP レート制限**: Defrago 側 (FastAPI) で同一 IP の頻度を制限する方が現実的
- **reCAPTCHA**: フォームに v3 を組み込む (やや実装コスト大)
- **ハニーポット**: フォームに hidden フィールドを仕込み、bot 除外

### GAS の再デプロイ

スクリプトを変更した場合、**新しいデプロイ** ではなく
**デプロイの管理** → 既存デプロイ右上の鉛筆アイコン → バージョンを
**新しいバージョン** に変更 → **デプロイ** することで **URL を変えずに**
スクリプトを更新できる。

新規デプロイしてしまうと URL が変わり、Render の環境変数の更新も必要に
なるので注意。

### Gmail 送信上限に注意

Google アカウント種別ごとの Gmail 送信上限:

- 個人 Google アカウント: 100 通/日 (`MailApp.sendEmail`)
- Google Workspace: 1,500 通/日

これを超えるとお問い合わせが届いても通知だけ飛ばなくなる (スプレッドシート
記録は継続される) ので、必要に応じてチェック。

## 5. 参考: Defrago 側の実装

本 GAS と連携する Defrago 側のコードは以下:

- 送信ロジック: [src/study_python/gtd/web/routers/iconbar.py](../src/study_python/gtd/web/routers/iconbar.py)
  の `submit_contact` エンドポイント
- 環境変数定義: [src/study_python/gtd/web/config.py](../src/study_python/gtd/web/config.py)
  の `contact_webhook_url`
- フォームテンプレート: [src/study_python/gtd/web/templates/partials/modal_contact.html](../src/study_python/gtd/web/templates/partials/modal_contact.html)
- テスト: [tests/gtd/web/test_iconbar.py](../tests/gtd/web/test_iconbar.py)
  の `TestContactEndpoint`
