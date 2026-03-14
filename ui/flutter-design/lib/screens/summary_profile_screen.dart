import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';

// ════════════════════════════════════════════════════════════
//  EKRAN 3 — Başarı Pop-up / Summary Modal
// ════════════════════════════════════════════════════════════

class WorkoutResult {
  final int reps;
  final int xp;
  final double speed; // rep/sec
  final String feedback;

  const WorkoutResult({
    required this.reps,
    required this.xp,
    required this.speed,
    required this.feedback,
  });
}

class SummaryModal extends StatelessWidget {
  final WorkoutResult result;
  final VoidCallback? onSave;

  const SummaryModal({super.key, required this.result, this.onSave});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.bgOverlay,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.bgSurface2,
              borderRadius: AppRadius.xl_,
              border: Border.all(color: AppColors.borderModal),
              boxShadow: [
                BoxShadow(
                  color: AppColors.brandGreen.withOpacity(0.08),
                  blurRadius: 40,
                  spreadRadius: 4,
                ),
              ],
            ),
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Trophy
                Container(
                  width: 48, height: 48,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A1500),
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.brandGold, width: 1.5),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.brandGold.withOpacity(0.2),
                        blurRadius: 16,
                      ),
                    ],
                  ),
                  child: const Icon(Icons.emoji_events, color: AppColors.brandGold, size: 22),
                ),
                const SizedBox(height: 12),
                Text('Antrenman Tamamlandı', style: AppTypography.displayMd),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(child: _StatCard(value: '${result.reps}', label: 'Tekrar', color: AppColors.brandGreen)),
                    const SizedBox(width: 8),
                    Expanded(child: _StatCard(value: '${result.xp}', label: 'XP', color: AppColors.brandGold)),
                    const SizedBox(width: 8),
                    Expanded(child: _StatCard(value: result.speed.toStringAsFixed(1), label: 'rep/sn', color: AppColors.brandBlue)),
                  ],
                ),
                const SizedBox(height: 18),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.bgCardFeedback,
                    borderRadius: AppRadius.md_,
                    border: Border.all(color: AppColors.borderFeedback),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'AI GERİ BİLDİRİM',
                        style: AppTypography.labelXs.copyWith(color: AppColors.brandGreen, letterSpacing: 1.5),
                      ),
                      const SizedBox(height: 6),
                      Text(result.feedback, style: AppTypography.labelSm.copyWith(color: AppColors.textSecondary, height: 1.5)),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: onSave,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.brandGreen,
                      foregroundColor: AppColors.bgBase,
                      shape: RoundedRectangleBorder(borderRadius: AppRadius.md_),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      elevation: 0,
                    ),
                    child: Text(
                      'Profile Kaydet & Devam Et',
                      style: AppTypography.bodyMd.copyWith(
                        color: AppColors.bgBase,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.5,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String value;
  final String label;
  final Color color;

  const _StatCard({required this.value, required this.label, required this.color});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
    decoration: BoxDecoration(
      color: AppColors.bgSurface3,
      borderRadius: AppRadius.md_,
    ),
    child: Column(
      children: [
        Text(value, style: AppTypography.statValue.copyWith(color: color)),
        const SizedBox(height: 4),
        Text(label.toUpperCase(), style: AppTypography.labelXs),
      ],
    ),
  );
}

// ════════════════════════════════════════════════════════════
//  EKRAN 4 — Profil Sayfası
//  Sade tasarım: Tarihe göre antrenman geçmişi (3–4 satır)
//  Her satır = 1 gün, toplam süre gösterilir
// ════════════════════════════════════════════════════════════

enum ActivityType { pushup, squat, other }

extension ActivityColor on ActivityType {
  Color get color {
    switch (this) {
      case ActivityType.pushup: return AppColors.brandGreen;
      case ActivityType.squat:  return AppColors.brandBlue;
      case ActivityType.other:  return AppColors.brandPurple;
    }
  }
  IconData get icon {
    switch (this) {
      case ActivityType.pushup: return Icons.fitness_center;
      case ActivityType.squat:  return Icons.accessibility_new;
      case ActivityType.other:  return Icons.sports_gymnastics;
    }
  }
  String get label {
    switch (this) {
      case ActivityType.pushup: return 'Şınav';
      case ActivityType.squat:  return 'Squat';
      case ActivityType.other:  return 'Egzersiz';
    }
  }
}

// Bir egzersizin detayı (detay sayfasında gösterilecek)
class ExerciseDetail {
  final String label;        // "50 Şınav"
  final ActivityType type;
  final int reps;
  final int durationSec;     // saniye cinsinden süre
  final int accuracy;

  const ExerciseDetail({
    required this.label,
    required this.type,
    required this.reps,
    required this.durationSec,
    required this.accuracy,
  });

  String get durationFormatted {
    final m = durationSec ~/ 60;
    final s = durationSec % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }
}

// Bir günlük antrenman oturumu
class TrainingSession {
  final String date;              // "Dün", "12.03.2025" vb.
  final String totalDuration;     // "03:55 dk"
  final int totalReps;
  final List<ExerciseDetail> exercises;

  const TrainingSession({
    required this.date,
    required this.totalDuration,
    required this.totalReps,
    required this.exercises,
  });
}

// ── Dummy veriler ─────────────────────────────────────────────
const _dummySessions = [
  TrainingSession(
    date: 'Dün',
    totalDuration: '03:55 dk',
    totalReps: 75,
    exercises: [
      ExerciseDetail(label: '50 Şınav', type: ActivityType.pushup, reps: 50, durationSec: 145, accuracy: 92),
      ExerciseDetail(label: '25 Squat', type: ActivityType.squat, reps: 25, durationSec: 90, accuracy: 88),
    ],
  ),
  TrainingSession(
    date: '12.03.2025',
    totalDuration: '02:10 dk',
    totalReps: 30,
    exercises: [
      ExerciseDetail(label: '30 Squat', type: ActivityType.squat, reps: 30, durationSec: 130, accuracy: 85),
    ],
  ),
  TrainingSession(
    date: '11.03.2025',
    totalDuration: '04:20 dk',
    totalReps: 82,
    exercises: [
      ExerciseDetail(label: '42 Şınav', type: ActivityType.pushup, reps: 42, durationSec: 148, accuracy: 90),
      ExerciseDetail(label: '40 Squat', type: ActivityType.squat, reps: 40, durationSec: 112, accuracy: 82),
    ],
  ),
  TrainingSession(
    date: '09.03.2025',
    totalDuration: '02:30 dk',
    totalReps: 60,
    exercises: [
      ExerciseDetail(label: '60 Şınav', type: ActivityType.pushup, reps: 60, durationSec: 150, accuracy: 94),
    ],
  ),
];

class ProfileScreen extends StatelessWidget {
  final String userName;
  final String leagueName;
  final List<TrainingSession> sessions;

  const ProfileScreen({
    super.key,
    this.userName = 'Pro-Developer',
    this.leagueName = 'Gümüş Lig',
    this.sessions = _dummySessions,
  });

  String get _initials =>
      userName.length >= 2 ? userName.substring(0, 2).toUpperCase() : userName.toUpperCase();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgBase,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 12),

            // ── Header: Avatar + kullanıcı bilgisi ──
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Row(
                children: [
                  // Avatar + kamera düzenleme ikonu
                  Stack(
                    children: [
                      Container(
                        width: 56, height: 56,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: const LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [AppColors.brandGreen, Color(0xFF1ABC9C)],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.brandGreen.withOpacity(0.3),
                              blurRadius: 16,
                              spreadRadius: 2,
                            ),
                          ],
                        ),
                        child: Center(
                          child: Text(
                            _initials,
                            style: const TextStyle(
                              color: AppColors.bgBase,
                              fontWeight: FontWeight.w700,
                              fontSize: 18,
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        right: 0, bottom: 0,
                        child: GestureDetector(
                          onTap: () {},
                          child: Container(
                            width: 22, height: 22,
                            decoration: BoxDecoration(
                              color: AppColors.brandGreen,
                              shape: BoxShape.circle,
                              border: Border.all(color: AppColors.bgBase, width: 2),
                            ),
                            child: const Icon(Icons.camera_alt, color: AppColors.bgBase, size: 11),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(userName, style: AppTypography.cardName.copyWith(fontSize: 17)),
                        const SizedBox(height: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1A1A28),
                            borderRadius: AppRadius.sm_,
                            border: Border.all(color: AppColors.borderPurple),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.shield, color: AppColors.brandPurple, size: 12),
                              const SizedBox(width: 4),
                              Text(
                                leagueName.toUpperCase(),
                                style: AppTypography.labelXs.copyWith(
                                  color: AppColors.brandPurple,
                                  letterSpacing: 1,
                                  fontSize: 9,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Divider
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              height: 0.5,
              color: AppColors.borderSubtle,
            ),

            const SizedBox(height: 20),

            // ── Antrenman Geçmişi başlık ──
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Text(
                'ANTRENMAN GEÇMİŞİ',
                style: AppTypography.labelXs.copyWith(
                  color: AppColors.textDimmed,
                  letterSpacing: 2,
                ),
              ),
            ),
            const SizedBox(height: 12),

            // ── Sade tarih bazlı liste (3–4 satır) ──
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                itemCount: sessions.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, index) {
                  final session = sessions[index];
                  return _SessionRow(
                    session: session,
                    onTap: () {
                      context.push('/activity-detail', extra: session);
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Session Row — bir günlük antrenman ────────────────────────
class _SessionRow extends StatelessWidget {
  final TrainingSession session;
  final VoidCallback? onTap;

  const _SessionRow({required this.session, this.onTap});

  @override
  Widget build(BuildContext context) {
    // Egzersiz tiplerinin renk noktaları
    final exerciseTypes = session.exercises.map((e) => e.type).toSet();

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.bgSurface2,
          borderRadius: AppRadius.lg_,
          border: Border.all(color: AppColors.borderSubtle),
        ),
        child: Row(
          children: [
            // Tarih ve egzersiz özeti
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Tarih
                  Text(
                    session.date,
                    style: AppTypography.cardName.copyWith(fontSize: 14),
                  ),
                  const SizedBox(height: 6),
                  // Egzersiz özetleri (renk noktalı)
                  Row(
                    children: [
                      ...exerciseTypes.map((type) => Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 6, height: 6,
                              decoration: BoxDecoration(
                                color: type.color,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              type.label,
                              style: AppTypography.activityMeta.copyWith(
                                color: AppColors.textSecondary,
                                fontSize: 10,
                              ),
                            ),
                          ],
                        ),
                      )),
                    ],
                  ),
                ],
              ),
            ),

            // Toplam süre + toplam tekrar
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  session.totalDuration,
                  style: AppTypography.bodyMd.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${session.totalReps} tekrar',
                  style: AppTypography.activityMeta.copyWith(fontSize: 10),
                ),
              ],
            ),
            const SizedBox(width: 8),

            // Chevron
            const Icon(Icons.chevron_right, color: AppColors.textMuted, size: 20),
          ],
        ),
      ),
    );
  }
}
