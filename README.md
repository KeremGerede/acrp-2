# Agentic DevOps Code Review and Functional Test Reporting Platform

SCM platformlarıyla entegre çalışan, multi-tenant ve web tabanlı bir **Agentic DevOps** platformu. Sistem; developer'ın yaptığı merge işlemlerini webhook ile algılar, değişen kodu **CodeReviewAgent** ile analiz eder, detaylı Türkçe rapor üretir, başarısız review durumunda pipeline'ı durdurur, functional test ve promotion akışını engeller, **RevertAgent** ile hatalı merge'i otomatik geri alır ve sonucu mail / PDF / dashboard üzerinden görünür hâle getirir.

> Bu proje **staj kapsamında adım adım geliştirilen** bir Agentic DevOps projesidir. Aşağıda anlatılanlar projenin **mevcut çalışan fazını** yansıtır; production-ready bir ürün iddiası taşımaz.

---

## 1. Proje Özeti

- **Multi-tenant** mimari: her kayıt `tenant_id` ile izole edilir.
- **Provider-adapter** mimarisi ile ilerler; platforma özel webhook payload'ları ortak bir internal event formatına dönüştürülür.
- **GitHub şu anda gerçek çalışan provider'dır.**
- **GitLab** ve **Azure DevOps** adapter'ları, ileride genişletilmek üzere **stub** olarak durmaktadır (`NotImplementedError`).
- Akış tamamen otomatiktir: developer merge yapar, gerisini sistem yürütür.

---

## 2. Projenin Amacı

Developer bir task branch'ini hedef/sprint branch'e merge ettiğinde sistem otomatik olarak:

- merge event'ini algılar,
- değişen dosyaları ve diff içeriğini çeker,
- **CodeReviewAgent** ile kodu inceler,
- **Review Rules** kurallarını dikkate alır,
- detaylı **Türkçe review raporu** üretir,
- **deterministic review policy** uygular,
- başarısız review durumunda **gate'i kapatır**,
- functional testleri **çalıştırmaz**,
- promotion / readiness akışını **engeller**,
- **RevertAgent** ile GitHub revert PR oluşturur,
- `AUTO_REVERT_MODE=create_and_merge_revert_pr` ise revert PR'ı **otomatik merge eder**,
- mail ve PDF raporu gönderir.

Amaç, manuel kod inceleme ve hatalı merge yönetimi sürecini azaltmak; bir merge'in kalite kapısından geçip geçmediğini otomatik, izlenebilir ve raporlanabilir hâle getirmektir.

---

## 3. Güncel Çalışan Akış

```
Developer task branch'i merge eder
  → GitHub pull_request.closed + merged=true webhook event'i gelir
  → event normalize edilir
  → task_to_sprint_merge algılanır
  → aynı merge'e ait duplicate push event varsa skip edilir
  → changed files / diff çekilir
  → MergeReviewRun oluşturulur
  → CodeReviewAgent değişen kodları inceler
  → Review Rules prompt'a dahil edilir
  → structured JSON review raporu üretilir
  → deterministic review policy uygulanır
  → Findings kaydedilir
  → Türkçe PDF / mail raporu oluşturulur
  → ReviewGateService sonucu değerlendirir
```

**Review approved ise:**
```
  → functional tests çalışabilir
  → test başarılıysa promotion / readiness akışı devam eder
```

**Review rejected ise:**
```
  → gate_status = blocked
  → functional tests skipped
  → promotion blocked
  → RevertAgent çalışır
  → GitHub revert PR oluşturulur
  → AUTO_REVERT_MODE=create_and_merge_revert_pr ise revert PR otomatik merge edilir
  → [MERGE REVERTED] maili gönderilir
```

---

## 4. Teknoloji Stack'i

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic / pydantic-settings
- Gemini LLM (`google-generativeai`)
- SMTP tabanlı EmailService
- GitHub REST + GraphQL API (`requests`)
- FPDF2 ile PDF rapor üretimi

### Frontend
- React
- Vite
- Tailwind CSS
- Axios
- React Router
- lucide-react ikonları

---

## 5. Mimari Katmanlar

| Katman | Açıklama |
|---|---|
| **Multi-Tenant Layer** | Her kayıt `tenant_id` ile izole edilir. |
| **Platform Integration Layer** | `ProjectIntegration` ile repo, branch pattern, webhook secret, mail alıcıları tanımlanır. |
| **Provider Adapter Layer** | GitHub aktif; GitLab/Azure stub. Platforma özel payload → ortak event. |
| **Webhook / Event Layer** | Gelen webhook'lar doğrulanır, normalize edilir, `SCMEventLog` olarak loglanır. |
| **Branch / Event Detection Layer** | Branch isimlerinden sprint/task çözümlenir, event türü tespit edilir. |
| **CodeReviewAgent Layer** | Diff üzerinden LLM destekli kod incelemesi. |
| **ReviewGate Layer** | Review sonucuna göre pipeline'ı açar/kapatır. |
| **RevertAgent Layer** | Reddedilen merge için revert PR oluşturur ve gerekirse otomatik merge eder. |
| **Functional Test Layer** | Sadece gate açıkken testleri çalıştırır. |
| **Report Layer** | Türkçe PDF / mail raporları üretir. |
| **Notification Layer** | SMTP üzerinden mail gönderir, `NotificationLog`'a yazar. |
| **Dashboard / UI Layer** | React tabanlı yönetim arayüzü. |
| **Logging & Status Tracking Layer** | `AgentStep` ile her adım izlenebilir şekilde loglanır. |

---

## 6. Provider Adapter Mimarisi

- **GitHubAdapter** → aktif çalışan adapter.
- **GitLabAdapter** ve **AzureDevOpsAdapter** → stub (genişletilebilir iskelet).
- Provider adapter'lar, platforma özel webhook payload'larını ortak bir **internal normalized event** formatına dönüştürür. Bu sayede pipeline'ın geri kalanı provider'dan bağımsız çalışır.

### Önemli normalized event alanları

| Alan | Açıklama |
|---|---|
| `provider` | Kaynak platform (örn. `github`) |
| `tenant_id` | Tenant kimliği |
| `integration_id` | Integration kimliği |
| `repository_full_name` | `owner/repo` formatında repo adı |
| `event_type` | Tespit edilen event türü |
| `actor_username` | İşlemi yapan kullanıcı |
| `source_branch` | Merge edilen kaynak branch |
| `target_branch` | Merge edilen hedef branch |
| `commit_sha` | Merge commit SHA |
| `pull_request_number` | PR numarası |
| `pull_request_node_id` | PR GraphQL node_id (revert için kritik) |
| `pull_request_url` | PR URL'i |
| `is_merge_event` | Merge event olup olmadığı |
| `raw_payload` | Orijinal webhook payload'ı |

---

## 7. GitHub Webhook Davranışı

Sistem şu anda **primary event** olarak şunu kullanır:

```
pull_request.closed + merged=true
```

Bu event tercih edilir çünkü PR metadata, source branch, target branch, merge commit SHA ve PR node_id gibi bilgileri daha güvenilir sağlar.

Ek davranışlar:

- **push event'leri** fallback / duplicate-skip mantığında kullanılır.
- **Duplicate merge event'leri** skip edilir (aynı `commit_sha` + `task_to_sprint_merge` daha önce işlendiyse).
- **Revert branch event'leri** skip edilir — sistem kendi oluşturduğu revert PR'ı tekrar review/revert etmez.

Skip edilen revert branch prefix'leri:

```
revert-
revert/
acrp-revert-
```

---

## 8. CodeReviewAgent

CodeReviewAgent'ın görevleri:

- Yalnızca **changed files / diff** üzerinden review yapar (diff dışındaki kodu uydurmaz).
- Şu alanlarda problem arar: bug, eksik logic, güvenlik açığı (SQL injection, XSS, hardcoded secret vb.), maintainability, code quality ve architecture.
- Aktif **Review Rules** kurallarını prompt'a dahil eder ve her bulguda ihlal edilen kuralı referans alır.
- **Structured JSON output** üretir.
- `findings` oluşturur.
- `passed_checks`, `failed_checks` ve `file_assessments` üretir.
- Çıktı dili **Türkçe**'dir; API, endpoint, controller, DTO, webhook, merge gibi teknik terimler İngilizce kalır.

LLM çıktısı, kaydedilmeden önce **normalize** edilir; geçersiz severity/category/status değerleri güvenli varsayılanlara çekilir.

---

## 9. Deterministic Review Policy

LLM kararına körü körüne güvenilmez. LLM çıktısı normalize edildikten sonra **deterministic policy** son kararı verir:

| Durum | Sonuç |
|---|---|
| `high` / `critical` severity finding | **rejected / failed** |
| `high` / `critical` severity Review Rule ihlali | **rejected / failed** |
| Sadece `warning` / `info` finding | approved / success |
| Hiç finding yok | approved / success |

Böylece LLM yanlışlıkla "success" dese bile, kritik bir bulgu varsa merge yine de reddedilir.

---

## 10. Review Raporu

Raporlar **Türkçe ve detaylıdır**. PDF ve mail raporu şu bölümleri içerir:

- **Detaylar**
- **Özet**
- **Karar Gerekçesi**
- **Bulgular**
- **Dosya Bazlı İnceleme Sonucu**
- **Başarıyla Geçen Kontroller**
- **Kalan / Düzeltilmesi Gereken Kısımlar**
- **İyileştirme Önerileri**

Notlar:

- Bulgular kısaltılmaz; finding açıklamaları detaylı gösterilir.
- Özet **kanıta dayalıdır** — sadece genel AI yorumu değil, diff ve bulgulara dayanan teknik bir değerlendirme sunar.
- Raporlar mail ekinde **PDF** olarak da gönderilir.

---

## 11. ReviewGateService

Review tamamlandıktan sonra pipeline'ın devam edip etmeyeceğine **ReviewGateService** karar verir.

**Review approved:**
- `gate_status = passed`
- functional tests çalışabilir
- promotion / readiness akışı devam edebilir

**Review rejected:**
- `gate_status = blocked`
- functional tests skipped
- promotion blocked
- `revert_required = true`
- RevertAgent tetiklenir

---

## 12. RevertAgent

RevertAgent'ın güncel çalışan davranışı:

1. Yalnızca **review rejected** olduktan sonra çalışır (gate blocked bloğu içinde).
2. `pull_request.closed` event'inden **PR node_id** bilgisini çözer (event log kolonu → REST → raw payload → commit lookup sırasıyla).
3. GitHub **GraphQL `revertPullRequest`** mutation'ı ile revert PR oluşturur.
4. Revert PR'ın **base branch'inin**, orijinal failed merge'in **target branch'i** ile aynı olduğunu doğrular.
5. `AUTO_REVERT_MODE=create_and_merge_revert_pr` ise GitHub REST API ile revert PR'ı otomatik merge eder:

   ```
   PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge
   ```

6. GitHub merge'i onaylarsa (`merged: true`) `revert_status = reverted` olur ve `[MERGE REVERTED]` maili gönderilir.

**Güvenlik kuralı:** GitHub merge işlemini onaylamadıkça `revert_status` asla `reverted` yapılmaz — sahte başarı raporlanmaz.

### Test edilen başarılı davranış

- Revert PR oluşturuldu.
- Revert PR otomatik merge edildi.
- GitHub PR durumu **Merged** olarak görüldü.
- Loglarda `PUT /pulls/{id}/merge status=200` görüldü.
- Duplicate push event skip edildi.
- System revert branch event'leri skip edildi.

---

## 13. Revert Mode Ayarları

`.env` içindeki ayar:

```
AUTO_REVERT_MODE=create_and_merge_revert_pr
```

Desteklenen değerler:

| Değer | Davranış |
|---|---|
| `disabled` | Sadece `revert_required` olarak işaretler, GitHub'da işlem yapmaz. |
| `create_revert_pr` | Revert PR oluşturur ve **açık bırakır** (manuel merge beklenir). |
| `create_and_merge_revert_pr` | Revert PR oluşturur ve **otomatik merge eder** (mevcut default). |

---

## 14. Functional Test Akışı

- Functional tests **yalnızca review approved ise** çalışır.
- Review gate `blocked` ise testler **skipped** olur (runner içinde ayrıca ikinci bir guard vardır).
- Test sonucu **deterministic** olarak runner output / **exit code** üzerinden belirlenir (`exit_code == 0` → success).
- LLM yalnızca test çıktısını **özetler**; tek karar kaynağı değildir.
- Test komutları operatör tarafından `FunctionalTestConfig` üzerinden tanımlanır ve `shell=False` ile, timeout'lu olarak çalıştırılır.

---

## 15. Promotion Akışı

- Promotion şu anda **otomatik deploy değildir.**
- Mevcut aşamada promotion, `ready_for_test_environment` anlamına gelir (TEST ortamına hazır işareti).
- Review failed ise promotion **blocked** olur ve izlenebilirlik için bir `blocked_by_review_gate` kaydı tutulur.
- Review success + functional test success sonrası promotion / readiness akışı devam eder ve `[PROMOTION READY]` maili gönderilir.

---

## 16. Notification Sistemi

- Mailler **SMTP tabanlı EmailService** ile gönderilir.
- Review raporları **PDF olarak mail ekinde** iletilir.
- Her mail için `NotificationLog` kaydı oluşturulur (`pending` → `sent` / `failed`).

Önemli mail subject örnekleri:

```
[REVIEW SUCCESS]
[REVIEW FAILED - MERGE BLOCKED]
[MERGE REVERTED]
[REVERT PR CREATED]
[REVERT FAILED]
[REVERT REQUIRED]
[TEST SUCCESS]
[TEST FAILED]
[PROMOTION READY]
```

---

## 17. Frontend

Mevcut sayfalar:

- **Dashboard**
- **Entegrasyonlar**
- **İnceleme Kuralları**
- **Test Yapılandırmaları**
- **Olay Günlükleri**
- **Birleştirme İncelemeleri**
- **Birleştirme İnceleme Detayı**
- **Fonksiyonel Testler**
- **Fonksiyonel Test Detayı**
- **Dağıtımlar (Promotions)**
- **Kullanıcı İstatistikleri**

Sidebar durumu:

- Koyu **AGENTDEVOPS** teması korunmuştur.
- Türkçe etiketli, ikonlu (lucide-react) sidebar uygulanmıştır.
- **Tenants menüsü sidebar'dan kaldırılmıştır.**
- Alt **Admin / Yönetici / Çıkış Yap** alanı yoktur.

---

## 18. Önemli Modeller

| Model | Açıklama |
|---|---|
| `Tenant` | Multi-tenant kök kayıt (ad, iletişim e-postası). |
| `ProjectIntegration` | Repo, provider, branch pattern'leri, webhook secret, mail alıcıları. |
| `SCMEventLog` | Gelen her webhook event'inin normalize edilmiş kaydı. |
| `MergeReviewRun` | Bir merge'e ait review çalışmasının tüm durumu (gate, revert dahil). |
| `Finding` | Review sırasında tespit edilen tekil bulgu. |
| `ReviewRule` | Tenant/integration bazlı, severity'li inceleme kuralları. |
| `FunctionalTestConfig` | Çalıştırılacak test komutu ve dizini. |
| `FunctionalTestRun` | Bir functional test çalışmasının sonucu. |
| `EnvironmentPromotionLog` | Promotion / readiness kayıtları (blocked dahil). |
| `NotificationLog` | Gönderilen mail kayıtları ve durumları. |
| `AgentStep` | Her agent adımının izlenebilir log kaydı. |
| `UserActivityStats` | Kullanıcı bazlı review/test/promotion sayaçları. |

---

## 19. Environment Variables

Aşağıdaki örnek değerleri `backend/.env` dosyasına kendi değerlerinizle doldurun:

```env
# LLM
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

# GitHub
GITHUB_TOKEN=your_github_token

# Webhook secret (varsayılan fallback; her integration kendi secret'ını da üretir)
DEFAULT_WEBHOOK_SECRET=your_webhook_secret

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email
SMTP_USE_TLS=true

# Revert davranışı
AUTO_REVERT_MODE=create_and_merge_revert_pr

# Diğer
DATABASE_URL=sqlite:///./agentic_devops.db
FRONTEND_URL=http://localhost:5173
```

Frontend için `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

> **Webhook secret notu:** Uygulama config'inde global bir `DEFAULT_WEBHOOK_SECRET` bulunur. Buna ek olarak, her `ProjectIntegration` oluşturulduğunda kendine ait bir `webhook_secret` otomatik üretilir ve `GET /api/integrations/{id}/webhook-info` üzerinden görüntülenir. GitHub webhook'unu kurarken bu integration secret'ı kullanılır.

> ⚠️ **Uyarı:** Gerçek `.env` dosyası ve secret değerleri **asla** GitHub'a commit edilmemelidir. `.env` ve veritabanı dosyaları `.gitignore` içinde tutulur; yalnızca `.env.example` commit edilir.

---

## 20. Kurulum Talimatları

### Backend

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt

# .env dosyasını hazırla
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# .env içine GEMINI_API_KEY, SMTP_*, GITHUB_TOKEN değerlerini gir

python run.py
# Backend: http://localhost:8000
# API dokümanı: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173
```

---

## 21. GitHub Webhook Kurulumu

GitHub repo → **Settings → Webhooks → Add webhook**:

- **Payload URL:**
  ```
  http://your-server/api/webhooks/github/{integration_id}
  ```
  (Lokal geliştirmede `ngrok http 8000` ile bir public URL kullanılabilir.)
- **Content type:** `application/json`
- **Secret:** integration webhook secret (webhook-info panelinden)
- **Events:** `Let me select individual events` → **Pull requests** + **Pushes**

> `pull_request.closed + merged=true`, review/revert akışı için **primary event** olarak kullanılır. `push` event'i fallback/duplicate-skip amacıyla değerlendirilir.

---

## 22. Bilinen Sınırlamalar ve Sonraki Geliştirmeler

Mevcut çalışan fazın üzerine planlanan iyileştirmeler:

- **Merge Review Detail** ekranında Gate / Revert durumlarını daha görünür hâle getirmek.
- Revert PR açıklama metnini otomatik merge davranışına uygun şekilde güncellemek.
- **Review Rules** sistemini instruction, auto_reject, file scope, template ve rule violation reporting ile güçlendirmek.
- **Integrations** ekranını sadeleştirmek ve repository branch discovery / sync eklemek.
- GitHub **status / check** entegrasyonu ile pre-merge gating eklemek.
- PDF **Türkçe karakter** desteğini iyileştirmek.
- GitHub **noreply** e-posta adreslerini filtrelemek ve configured recipient fallback kullanmak.
- **Dashboard** görünürlüğünü geliştirmek.
- İleride daha güçlü **event idempotency / locking** mekanizması eklemek.

---

## 23. Notlar

- Sistem merge işlemini kendisi başlatmaz; yalnızca tamamlanmış merge'lere webhook üzerinden **tepki verir**.
- Otomatik conflict çözümü, otomatik deployment veya harici iş kuyruğu (Celery/Redis vb.) **bulunmamaktadır.**
- Bu doküman, projenin **staj kapsamında adım adım geliştirilen mevcut çalışan fazını** anlatır.
