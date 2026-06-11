# Agentic DevOps Code Review and Functional Test Reporting Platform

Bu proje, CI/CD süreçlerinde **AI destekli code review**, **functional test raporlama**, **promotion kontrolü** ve **otomatik revert** yaklaşımlarını tek bir web tabanlı platformda birleştiren, multi-tenant bir sistemdir.

---

## 1. Proje Hakkında

**Amaç:** Bir task branch'i sprint branch'e merge edildiğinde, değişen kodu otomatik olarak incelemek, kalite kapısından (gate) geçirmek, başarısız durumda pipeline'ı durdurup hatalı merge'i geri almak ve tüm bu süreci mail/PDF raporu ile görünür kılmak.

**Çözdüğü problem:** Manuel kod inceleme ve hatalı merge yönetimi zaman alır ve insana bağımlıdır. Bu platform; review kararını, gate davranışını, functional test/promotion akışını ve revert sürecini otomatikleştirir, izlenebilir hâle getirir.

**CI/CD içindeki konumu:**
- **AI code review:** Merge sonrası değişen diff incelenir, yapay zekâ ile bulgular üretilir.
- **Functional test reporting:** Review onaylandıysa fonksiyonel testler çalıştırılıp raporlanır.
- **Promotion:** Test başarılıysa değişiklik DEV/TEST ortamına "hazır" olarak işaretlenir.
- **Auto-revert:** Review başarısızsa hatalı merge için revert PR oluşturulur ve (yapılandırmaya göre) otomatik merge edilir.

**Yapı:** Sistem multi-tenant'tır (her kayıt `tenant_id` ile izole edilir) ve web tabanlı bir arayüze sahiptir. Merge işlemini sistem başlatmaz; tamamlanmış merge'lere webhook üzerinden **tepki verir**.

---

## 2. Projenin Genel Akışı

```
Developer task branch üzerinde çalışır
  → Task branch sprint branch'e merge edilir (Pull Request merge)
  → GitHub webhook event'i gelir (pull_request.closed + merged=true)
  → Sistem event'i normalize eder (ortak internal event formatı)
  → task_to_sprint_merge olarak algılanır
  → Changed files / diff GitHub API ile çekilir
  → MergeReviewRun kaydı oluşturulur
  → AI code review agent (ReviewerAgent) çalışır
  → Review rules prompt'a dahil edilir
  → Structured JSON review çıktısı üretilir
  → Deterministic review policy uygulanır
  → Findings veritabanına kaydedilir
  → Mail/PDF raporu oluşturulur
  → ReviewGateService kararı verir
```

**Review başarılıysa:** gate `passed` → functional test çalışabilir → test başarılıysa promotion/readiness kaydı oluşturulur.

**Review başarısızsa:** gate `blocked` → functional test skipped → promotion blocked → RevertAgent tetiklenir → revert PR oluşturulur → (auto-merge modunda) otomatik merge edilir.

---

## 3. Kullanılan Teknolojiler

### Backend
- **Python**
- **FastAPI** (web framework, `BackgroundTasks` ile arka plan pipeline)
- **SQLAlchemy** (ORM)
- **SQLite** (varsayılan veritabanı — `DATABASE_URL` ile değiştirilebilir; projede yalnızca SQLite kullanılmaktadır)
- **Pydantic / pydantic-settings** (şema ve konfigürasyon)
- **Gemini LLM** (`google-generativeai`) — code review ve test özeti
- **SMTP tabanlı EmailService** (mail bildirimleri)
- **GitHub REST + GraphQL API** (`requests`) — diff çekme, revert PR oluşturma/merge
- **FPDF2** (PDF rapor üretimi)

> Not: Projede LangGraph, Celery veya Redis gibi bir orkestrasyon/iş kuyruğu **kullanılmamaktadır**. Arka plan işleri FastAPI `BackgroundTasks` ile yürütülür.

### Frontend
- **React**
- **Vite**
- **Tailwind CSS**
- **Axios**
- **React Router**
- **lucide-react** (ikonlar)

### DevOps / Entegrasyon
- **GitHub webhook** (aktif çalışan provider)
- **Provider-adapter mimarisi** (GitLab / Azure DevOps için genişletilebilir iskelet)
- **Branch bazlı review ve promotion akışı**

---

## 4. Mimari Yapı

### Backend

- **API route katmanı** (`app/api/routes/`): REST endpoint'leri ve webhook endpoint'i.
- **Webhook endpoint'i** (`webhooks.py`): Gelen event'i doğrular, normalize eder, `SCMEventLog` olarak loglar ve pipeline'ı tetikler.
- **Provider adapter katmanı** (`app/providers/`): Platforma özel webhook payload'larını ortak event formatına çeviren adapter'lar.
- **ReviewerAgent** (`app/agents/reviewer_agent.py`): Review rule'ları yükler, diff'i prompt'a dönüştürür, LLM'i çağırır, çıktıyı normalize edip deterministic policy uygular.
- **Functional test runner** (`app/services/functional_test_runner_service.py` + `app/agents/functional_test_agent.py`): Yapılandırılmış test komutunu çalıştırır, exit code'a göre sonucu belirler.
- **Promotion** (`functional_test_runner_service.py` içinde): Test başarılıysa `EnvironmentPromotionLog` kaydı oluşturur.
- **RevertAgent** (`app/agents/revert_agent.py` + `app/services/revert_service.py`): Başarısız review sonrası revert PR oluşturur ve (yapılandırmaya göre) otomatik merge eder.
- **ReviewGateService** (`app/services/review_gate_service.py`): Review sonucuna göre gate kararını verir.
- **Veritabanı modelleri** (`app/models/`): Aşağıda Bölüm 9'da listelenmiştir.
- **Mail/PDF rapor servisleri** (`email_service.py`, `pdf_report_service.py`).

### Frontend

Mevcut sayfalar (`frontend/src/pages/`):
- **Dashboard**
- **Entegrasyonlar** (Integrations)
- **İnceleme Kuralları** (Review Rules)
- **Test Yapılandırmaları** (Functional Test Configs)
- **Olay Günlükleri** (Event Logs)
- **Birleştirme İncelemeleri** (Merge Reviews) + **Birleştirme İnceleme Detayı**
- **Fonksiyonel Testler** (Functional Tests) + **Fonksiyonel Test Detayı**
- **Dağıtımlar / Promotions**
- **Kullanıcı İstatistikleri** (User Stats)

> **Sidebar durumu:** Koyu AGENTDEVOPS teması kullanılır; Tenants sayfası route olarak vardır ancak sidebar menüsünden gizlenmiştir.
>
> **Planlanan/henüz yok:** "Test Yükleme", "Sprint Detayları" ve "Task Mergeability / Görev Uygunluk Durumu" ekranları **mevcut değildir**; gelecekte eklenmesi planlanmaktadır.

---

## 5. Provider-Adapter Yapısı

Adapter'lar `app/providers/` altındadır ve platforma özel webhook payload'larını ortak bir **normalized event** formatına dönüştürür. Böylece pipeline'ın geri kalanı provider'dan bağımsız çalışır.

- **GitHubAdapter** → **gerçek çalışan** adapter. Webhook parse, diff/commit çekme, revert PR işlemleri burada uygulanır.
- **GitLabAdapter** → **stub** (geliştirme aşaması; `NotImplementedError`).
- **AzureDevOpsAdapter** → **stub** (geliştirme aşaması; `NotImplementedError`).

**Amaç:** SCM platformlarına bağımlılığı azaltmak ve yeni sağlayıcı eklemeyi kolaylaştırmak.

**Yeni provider ekleme:** `ProviderAdapter` temel sınıfından türeyen yeni bir adapter yazılır, `parse_webhook_event` ve diff çekme metotları implemente edilir ve `registry.py` üzerinden kaydedilir.

---

## 6. Code Review Mantığı

**Review'ı ne başlatır?**
- Review **yalnızca** `pull_request.closed + merged=true` event'i ile başlar (bu event PR numarası, source/target branch, merge commit SHA ve PR node_id taşır).
- **Push event'leri review başlatmaz.** Push event'leri yalnızca loglanır; PR numarası olmadığı için pipeline'ı tetiklemez ve sonradan gelen PR event'ini de engellemez.

**Akış:**
1. Merge edilen PR'ın `before/after` SHA'ları üzerinden changed files/diff GitHub API ile çekilir (compare → commit fetch fallback'leri ile).
2. Aktif **Review Rules** prompt'a dahil edilir.
3. LLM prompt'una merge bağlamı (repo, sprint, task, branch'ler), kurallar ve diff eklenir.
4. LLM **structured JSON** döndürür (findings, passed_checks, failed_checks, file_assessments, summary, decision_reason).
5. Çıktı `review_report_normalizer_tool` ile normalize edilir (geçersiz severity/category değerleri güvenli varsayılana çekilir).

**Deterministic review policy** (`review_decision_policy_tool.py`) — LLM kararına körü körüne güvenilmez:
- **Critical** finding varsa → rejected/failed
- **High** finding varsa → rejected/failed
- **High/Critical** seviyeli Review Rule ihlali varsa → rejected/failed
- Sadece **warning/info** finding varsa → approved/success
- Hiç finding yoksa → approved/success

> **Boş diff koruması:** Diff alınamadıysa veya changed_files boşsa kod gerçekten incelenmemiş demektir. Bu durumda sistem "finding yok → success" sonucuna **gitmez**; review failed olarak işaretlenir ve gate bloklanır (fake success üretilmez). Bu koruma kodda mevcuttur.

---

## 7. Review Failed ve Auto-Revert Akışı

Review başarısız olduğunda:
- `gate_status = blocked`
- functional test **skipped**
- promotion **blocked**
- İzlenebilirlik için `EnvironmentPromotionLog` üzerinde `blocked_by_review_gate` kaydı oluşturulur
- **RevertAgent tetiklenir**
- Mail/PDF raporu gönderilir
- Functional test çalışmaz, promotion/readiness kaydı oluşturulmaz

**Auto-revert (kodda mevcut ve çalışıyor):**
- `pull_request.closed` event'inden PR node_id çözülür.
- GitHub **GraphQL `revertPullRequest`** mutation'ı ile revert PR oluşturulur.
- Revert PR'ın base branch'inin, orijinal failed merge'in target branch'i ile aynı olduğu doğrulanır.
- `AUTO_REVERT_MODE=create_and_merge_revert_pr` ise revert PR GitHub REST API (`PUT /repos/{owner}/{repo}/pulls/{n}/merge`) ile **otomatik merge edilir**.
- GitHub merge'i onaylarsa `revert_status = reverted` olur; aksi halde `revert_failed` / `revert_conflict` / `required` gibi değerlerle ayrılır. (GitHub onaylamadıkça `reverted` yazılmaz.)
- **Revert branch skip:** Sistemin kendi oluşturduğu `revert-`, `revert/`, `acrp-revert-` ile başlayan branch event'leri review/revert akışına **sokulmaz** (sonsuz döngü engellenir).

`AUTO_REVERT_MODE` değerleri: `disabled`, `create_revert_pr`, `create_and_merge_revert_pr`.

---

## 8. Dev/Test Mergeability Mantığı

> **Durum:** Bu bölümde anlatılan model **henüz kodda uygulanmamıştır**; mevcut çalışan Agentic DevOps yapısından bu projeye taşınacak/eklenmesi planlanan **hedef tasarımdır**. Aşağıdaki kurallar gelecekteki davranışı tanımlar.

**Seçilen model:** "Default true + eligibility/pool kontrolü + sprint blocking".

**Dev tarafı kuralları:**
- Her task başlangıçta `dev_mergeable=true` ve `test_mergeable=true` kabul edilebilir.
- Ancak henüz sprint branch'e merge edilmemiş task'lar **karar havuzuna dahil edilmez**.
- Dev promotion havuzuna yalnızca sprint'e merge edilmiş, review sürecinden geçmiş ve dev'e henüz promote edilmemiş **aktif** task'lar dahil edilir.
- Bu havuzda **bir tane bile** `dev_mergeable=false` varsa, sprint → dev promotion **blocked** olur.
- Failed task düzeltilip yeniden successful review alırsa `dev_mergeable=true` olur.
- Havuzdaki tüm aktif task'lar true olduğunda sprint branch dev ortamına merge edilebilir.

**Test tarafı kuralları:**
- Test senaryoları manuel yüklenebilir.
- Task'lar tek tek veya grup olarak seçilebilir.
- Bir test senaryosu `required_task_ids=[...]` mantığıyla çalışmalıdır (örn. task3 ve task4 birlikte test edilecekse).
- **Count tek başına karar vermemelidir**; aksi halde task2 + task3 gibi yanlış kombinasyonlar count'u doldurup hatalı test başlatabilir.
- Doğru karar, ilgili test senaryosundaki **required task'ların tamamının** dev ortamında bulunup bulunmadığına göre verilmelidir.

---

## 9. Veri Yapısı / Veri Setleri

> Bu projede klasik anlamda bir **ML veri seti kullanılmamıştır**. Sistem, statik bir veri seti üzerinde eğitilmez; canlı SCM verileri ve LLM çıktıları üzerinde çalışır.

Kullanılan veri kaynakları:
- Pull request / merge metadata (numara, node_id, branch'ler, merge commit SHA)
- Changed files ve git diff içeriği
- Review rules (tenant/integration bazlı kurallar)
- Webhook event logları (`SCMEventLog`)
- Task, sprint ve promotion kayıtları
- LLM review çıktıları (findings, checks, file assessments)
- Functional test sonuçları
- PDF/mail rapor içerikleri

**Veritabanı modelleri** (`app/models/`):
- `Tenant` — multi-tenant kök kayıt
- `ProjectIntegration` — repo, provider, branch pattern'leri, webhook secret, mail alıcıları
- `PlatformCredential` — entegrasyona ait token
- `SCMEventLog` — normalize edilmiş webhook event kaydı
- `MergeReviewRun` — bir merge'e ait review/gate/revert durumu
- `Finding` — tekil review bulgusu
- `ReviewRule` — severity'li inceleme kuralları
- `FunctionalTestConfig` / `FunctionalTestRun` — test komutu ve çalışma sonucu
- `EnvironmentPromotionLog` — promotion / readiness (blocked dahil)
- `NotificationLog` — mail kayıtları ve durumları
- `AgentStep` — her agent adımının izlenebilir logu
- `UserActivityStats` — kullanıcı bazlı review/test/promotion sayaçları
- `Repository`, `SyncedSprint`, `SyncedTask` — temel/yardımcı yapılar (sprint/task senkronizasyonu için iskelet; sync endpoint'i şu an **stub**)

> Projede ayrı bir seed/sample veri scripti veya örnek zafiyetli kod dosyası gözlemlenmemiştir.

---

## 10. Karşılaşılan Sorunlar ve Çözümler

- **Push event'in yanlışlıkla review akışını başlatma riski**
  - **Çözüldü:** Review yalnızca PR merge event'i (`pull_request.closed + merged=true`, PR numarası taşıyan) üzerinden tetiklenir. Push event'leri yalnızca loglanır.
- **Empty diff / changed_files boş gelme riski**
  - **Çözüldü:** Diff boşsa fake success üretilmemesi için guard eklendi; review failed olarak işaretlenir ve gate bloklanır.
- **Review failed sonrası hatalı kodun sprint branch'te kalması**
  - **Çözüldü:** Auto-revert mekanizması ile failed merge için revert PR oluşturulur ve (auto-merge modunda) otomatik merge edilir.
- **Aynı merge için duplicate review/revert riski (PR + push birlikte gelince)**
  - **Çözüldü:** Dedup `pull_request_number` üzerinden yapılır; aynı PR'ın tekrar gelen event'i atlanır, push event PR event'ini bloklamaz.
- **Repository identifier'ının yanlış formatta (URL) gelmesi**
  - **Çözüldü:** Tüm GitHub API çağrılarından önce repo adı `owner/repo` formatına normalize edilir.
- **Default true mergeability'nin yanlış task'ları karar havuzuna sokma riski**
  - **Planlandı:** Eligibility/pool kontrolü ile yalnızca sprint'e merge edilmiş aktif task'ların havuza dahil edilmesi tasarlandı (Bölüm 8). Bu kısım henüz kodda uygulanmadı.
- **Test scenario count problemi**
  - **Planlandı:** Count yerine `required_task_ids` / TaskTest ilişkisi kullanılması tasarlandı; henüz uygulanmadı.
- **Provider bağımlılığı**
  - **Çözüldü (temel):** Provider-adapter mimarisi kuruldu; GitHub aktif, GitLab/Azure DevOps stub.

---

## 11. Kurulum

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# veya
source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

`.env` dosyası (örnek — `backend/.env.example` baz alınarak doldurulmalı). Aşağıdakiler projede gerçekten okunan değişkenlerdir:

```env
DATABASE_URL=sqlite:///./agentic_devops.db
FRONTEND_URL=http://localhost:5173

LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email
SMTP_USE_TLS=true

DEFAULT_WEBHOOK_SECRET=change-me
GITHUB_TOKEN=your_github_token
AUTO_REVERT_MODE=create_and_merge_revert_pr
```

> Not: Her entegrasyon (`ProjectIntegration`) oluşturulduğunda kendine ait bir `webhook_secret` otomatik üretilir ve `GET /api/integrations/{id}/webhook-info` ile görüntülenir. GitHub webhook'u kurulurken bu secret kullanılır. `GITLAB_TOKEN` / `WEBHOOK_SECRET` gibi değişkenler **kodda kullanılmadığından** burada yer almaz.
>
> ⚠️ Gerçek `.env` ve secret değerleri repoya commit edilmemelidir (`.env` ve `.db` dosyaları `.gitignore` içindedir).

Backend çalıştırma:

```bash
python run.py
# Backend: http://localhost:8000  | API docs: http://localhost:8000/docs
```

Alternatif:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173
```

Frontend `.env.local` (API adresi):

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 12. Proje Nasıl Kullanılır?

1. **Entegrasyon oluştur:** Entegrasyonlar sayfasından provider (`github`) ve repository bilgilerini gir.
2. **Repository/provider bilgilerini gir:** `repository_full_name` (örn. `owner/repo`), branch pattern'leri, mail alıcıları.
3. **Webhook URL al:** `GET /api/integrations/{id}/webhook-info` ile webhook URL'i ve secret'ı görüntüle.
4. **GitHub tarafında webhook tanımla:** Payload URL `…/api/webhooks/github/{integration_id}`, content type `application/json`, secret ve "Pull requests" + "Pushes" event'leri.
5. **Review rules ekle:** İnceleme Kuralları sayfasından kurallar tanımla.
6. **Merge yap:** Task branch → sprint branch PR'ını GitHub'da merge et.
7. **Review sonucunu takip et:** Birleştirme İncelemeleri sayfasından sonucu ve detayını izle.
8. **Failed durumu gör:** Başarısız review'da rapor, gate ve revert durumunu incele.
9. **Test senaryosu yükle:** Test Yapılandırmaları sayfasından test komutunu tanımla.
10. **Promotion durumunu takip et:** Dağıtımlar sayfasından promotion/readiness kayıtlarını izle.

---

## 13. API Endpointleri

> Kimlik doğrulama (auth) katmanı bu fazda **bulunmamaktadır**; auth endpoint'i yoktur.

- **Health:** `GET /api/debug/health`
- **Tenants:** `GET/POST /api/tenants`
- **Integrations:** `GET /api/integrations`, `POST /api/integrations`, `GET/PATCH/DELETE /api/integrations/{id}`, `GET /api/integrations/{id}/webhook-info`, `POST /api/integrations/{id}/sync` (stub)
- **Review Rules:** `GET/POST /api/review-rules`, `PATCH/DELETE /api/review-rules/{id}`, `PATCH /api/review-rules/{id}/toggle`
- **Functional Test Configs:** `GET/POST /api/functional-test-configs`, `PATCH/DELETE /api/functional-test-configs/{id}`, `PATCH /api/functional-test-configs/{id}/toggle`
- **Webhooks:** `POST /api/webhooks/{provider}/{integration_id}`
- **Events:** `GET /api/events`, `GET /api/events/{id}`
- **Merge Reviews:** `GET /api/merge-reviews`, `GET /api/merge-reviews/{id}`, `GET /api/merge-reviews/{id}/findings`, `GET /api/merge-reviews/{id}/steps`, `GET /api/merge-reviews/{id}/report-data`, `GET /api/merge-reviews/{id}/pdf`
- **Functional Tests:** `GET /api/functional-tests`, `GET /api/functional-tests/{id}`
- **Promotions:** `GET /api/promotions`, `GET /api/promotions/{id}`
- **Notifications:** `GET /api/notifications`, `GET /api/notifications/merge-reviews/{id}`, `GET /api/notifications/functional-tests/{id}`
- **Stats:** `GET /api/stats/users`

---

## 14. Mevcut Durum

**Çalışan kısımlar:**
- Dashboard ve yönetim arayüzü (React)
- Entegrasyon yönetimi
- Review rules yönetimi
- Webhook event logging (`SCMEventLog`)
- AI code review (ReviewerAgent + Gemini)
- Deterministic review policy
- Boş diff guard (fake success engelleme)
- PR-only review trigger (push event review başlatmaz)
- Duplicate event koruması (`pull_request_number` bazlı dedup)
- Repository normalizasyonu (`owner/repo`)
- Functional test / promotion temel yapısı
- Mail/PDF raporlama (üst durum kutusu dahil)
- **Auto-revert** (revert PR oluşturma + otomatik merge + revert branch skip)

**Eksik / geliştirilecek kısımlar:**
- Dev/Test Mergeability modeli ve mantığı (Bölüm 8 — henüz kodda yok)
- Task Mergeability frontend görünümü
- Test scenario dependency yönetimi (`required_task_ids` / TaskTest)
- Provider genişletmeleri (GitLab / Azure DevOps stub durumda)
- Merge Review Detail ekranında gate/revert durumunun daha görünür yapılması
- Sprint/Task senkronizasyonu (sync endpoint'i stub)
- Role-based access control (RBAC) ve auth

---

## 15. Gelecek Geliştirmeler

- GitHub/GitLab/Azure DevOps provider desteğini genişletme
- Auto-revert entegrasyonunu güçlendirme
- Dedup mekanizmasını iyileştirme (webhook redelivery senaryoları)
- Task Mergeability ekranı
- Test scenario dependency yönetimi
- Daha detaylı PDF/mail durum blokları
- Daha kapsamlı audit log
- Role-based access control (RBAC)
- Production deployment hazırlığı

---

## 16. Klasör Yapısı

```text
backend/
  app/
    agents/        # reviewer_agent, functional_test_agent, revert_agent
    api/
      routes/      # webhook + REST endpoint'leri
    core/          # config, security
    db/            # database, migrations
    models/        # SQLAlchemy modelleri
    providers/     # github_adapter, gitlab_adapter(stub), azure_devops_adapter(stub),
                   # base, registry, normalized_events
    schemas/       # Pydantic şemaları
    services/      # review_gate, revert_service, email_service,
                   # functional_test_runner, pdf_report, llm_service, ...
    tools/         # review_rule_loader, changed_files_fetcher,
                   # review_decision_policy, review_report_normalizer, functional_test_report
    main.py
  run.py
  requirements.txt
  .env.example
frontend/
  src/
    api/           # client.js (axios)
    components/    # Layout, Badge, Loading, ErrorMessage
    pages/         # Dashboard, Integrations, ReviewRules, FunctionalTestConfigs,
                   # EventLogs, MergeReviews, MergeReviewDetail, FunctionalTests,
                   # FunctionalTestDetail, Promotions, UserStats, Tenants
    App.jsx
    main.jsx
  package.json
README.md
```

---

## 17. Sonuç

Bu proje, staj kapsamında adım adım geliştirilen ve CI/CD süreçlerinde AI destekli code review, functional test yönetimi, promotion kontrolü ve auto-revert yaklaşımını birleştiren web tabanlı, multi-tenant bir platformdur. İlk çalışan fazda temel review, gate, raporlama ve auto-revert mantıkları kurulmuş; provider-adapter mimarisi ile genişlemeye hazır hâle getirilmiştir. Sonraki aşamalarda Dev/Test mergeability modeli, test dependency yönetimi, ek provider desteği ve frontend görünürlükleri geliştirilecektir.
