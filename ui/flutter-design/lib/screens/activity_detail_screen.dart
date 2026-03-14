import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme/app_theme.dart';
import 'summary_profile_screen.dart';

// ════════════════════════════════════════════════════════════
//  Aktivite Detay Sayfası (ActivityDetailScreen)
//  Bir günün egzersiz detayları: tekrar, süre, doğruluk
//  + Haftalık performans grafiği
// ════════════════════════════════════════════════════════════

class ActivityDetailScreen extends StatelessWidget {
  final dynamic item; // TrainingSession

  const ActivityDetailScreen({super.key, this.item});

  @override
  Widget build(BuildContext context) {
    final session = item is TrainingSession
        ? item as TrainingSession
        : const TrainingSession(
            date: 'Dün',
            totalDuration: '03:55 dk',
            totalReps: 75,
            exercises: [
              ExerciseDetail(label: '50 Şınav', type: ActivityType.pushup, reps: 50, durationSec: 145, accuracy: 92),
              ExerciseDetail(label: '25 Squat', type: ActivityType.squat, reps: 25, durationSec: 90, accuracy: 88),
            ],
          );

    return Scaffold(
      backgroundColor: AppColors.bgBase,
      body: SafeArea(
        child: Column(
          children: [
            // ── Üst bar ──
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: Container(
                      width: 36, height: 36,
                      decoration: BoxDecoration(
                        color: AppColors.bgSurface2,
                        borderRadius: AppRadius.md_,
                        border: Border.all(color: AppColors.borderSubtle),
                      ),
                      child: const Icon(Icons.arrow_back_ios_new, color: AppColors.textPrimary, size: 16),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          session.date,
                          style: AppTypography.cardName.copyWith(fontSize: 16),
                        ),
                        Text(
                          '${session.totalDuration}  ·  ${session.totalReps} tekrar',
                          style: AppTypography.activityMeta.copyWith(fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 8),

                    // ── Egzersiz detay kartları ──
                    Text(
                      'EGZERSİZLER',
                      style: AppTypography.labelXs.copyWith(
                        color: AppColors.textDimmed,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 10),

                    ...session.exercises.map((ex) => _ExerciseDetailCard(exercise: ex)),

                    const SizedBox(height: 24),

                    // ── Toplam özet kartları (3'lü) ──
                    Text(
                      'TOPLAM ÖZET',
                      style: AppTypography.labelXs.copyWith(
                        color: AppColors.textDimmed,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: _SummaryStatCard(
                            icon: Icons.repeat,
                            value: '${session.totalReps}',
                            label: 'Tekrar',
                            color: AppColors.brandGreen,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: _SummaryStatCard(
                            icon: Icons.timer_outlined,
                            value: session.totalDuration.replaceAll(' dk', ''),
                            label: 'Süre',
                            color: AppColors.brandBlue,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: _SummaryStatCard(
                            icon: Icons.star_outline,
                            value: _avgAccuracy(session),
                            label: 'Ort. Doğruluk',
                            color: AppColors.brandGold,
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ── Haftalık performans grafiği ──
                    Text(
                      'HAFTALIK PERFORMANS',
                      style: AppTypography.labelXs.copyWith(
                        color: AppColors.textDimmed,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      height: 200,
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.bgSurface2,
                        borderRadius: AppRadius.lg_,
                        border: Border.all(color: AppColors.borderSubtle),
                      ),
                      child: const _WeeklyPerformanceChart(
                        accentColor: AppColors.brandGreen,
                      ),
                    ),

                    const SizedBox(height: 24),

                    // ── AI Analiz notu ──
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.bgCardFeedback,
                        borderRadius: AppRadius.md_,
                        border: Border.all(color: AppColors.borderFeedback),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.auto_awesome, color: AppColors.brandGreen, size: 14),
                              const SizedBox(width: 6),
                              Text(
                                'AI Değerlendirmesi',
                                style: AppTypography.labelSm.copyWith(
                                  color: AppColors.brandGreen,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _getSessionFeedback(session),
                            style: AppTypography.labelSm.copyWith(
                              color: AppColors.textSecondary,
                              height: 1.6,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _avgAccuracy(TrainingSession s) {
    if (s.exercises.isEmpty) return '0%';
    final avg = s.exercises.map((e) => e.accuracy).reduce((a, b) => a + b) / s.exercises.length;
    return '%${avg.round()}';
  }

  String _getSessionFeedback(TrainingSession session) {
    final avg = session.exercises.isEmpty
        ? 0
        : session.exercises.map((e) => e.accuracy).reduce((a, b) => a + b) / session.exercises.length;
    if (avg >= 90) {
      return 'Harika bir antrenman günü! Tüm egzersizlerde form ve tekrar açısından üst düzey bir performans sergilledin. Bu tempoda devam et.';
    } else if (avg >= 80) {
      return 'İyi bir antrenman. Genel olarak formun sağlamdı. Bazı egzersizlerde son tekrarlarda daha dikkatli olmayı dene, doğruluk oranını daha da yukarı çekebilirsin.';
    } else {
      return 'Formun bazı egzersizlerde zayıfladı. Daha kontrollü ve yavaş tekrarlar yapmayı dene. Kalite her zaman miktardan önemlidir.';
    }
  }
}

// ── Egzersiz detay kartı ──────────────────────────────────────
class _ExerciseDetailCard extends StatelessWidget {
  final ExerciseDetail exercise;

  const _ExerciseDetailCard({required this.exercise});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.bgSurface2,
        borderRadius: AppRadius.lg_,
        border: Border.all(color: AppColors.borderSubtle),
      ),
      child: Row(
        children: [
          // Tip ikonu
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              color: exercise.type.color.withOpacity(0.12),
              borderRadius: AppRadius.md_,
            ),
            child: Icon(exercise.type.icon, color: exercise.type.color, size: 22),
          ),
          const SizedBox(width: 14),

          // Bilgiler
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  exercise.label,
                  style: AppTypography.cardName.copyWith(fontSize: 14),
                ),
                const SizedBox(height: 4),
                // Süre bilgisi — saniye cinsinden
                Row(
                  children: [
                    const Icon(Icons.timer_outlined, color: AppColors.textMuted, size: 12),
                    const SizedBox(width: 4),
                    Text(
                      '${exercise.durationFormatted} dk  ·  ${exercise.reps} tekrar',
                      style: AppTypography.activityMeta.copyWith(fontSize: 10, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Doğruluk badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: exercise.type.color.withOpacity(0.12),
              borderRadius: AppRadius.sm_,
            ),
            child: Text(
              '%${exercise.accuracy}',
              style: TextStyle(
                color: exercise.type.color,
                fontWeight: FontWeight.w700,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Summary stat card (3'lü) ──────────────────────────────────
class _SummaryStatCard extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _SummaryStatCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 6),
    decoration: BoxDecoration(
      color: AppColors.bgSurface2,
      borderRadius: AppRadius.md_,
      border: Border.all(color: AppColors.borderSubtle),
    ),
    child: Column(
      children: [
        Icon(icon, color: color, size: 18),
        const SizedBox(height: 8),
        Text(value, style: AppTypography.statValue.copyWith(color: color, fontSize: 20)),
        const SizedBox(height: 4),
        Text(
          label.toUpperCase(),
          style: AppTypography.labelXs.copyWith(letterSpacing: 0.5, fontSize: 7),
          textAlign: TextAlign.center,
        ),
      ],
    ),
  );
}

// ── Haftalık performans grafiği ───────────────────────────────
class _WeeklyPerformanceChart extends StatelessWidget {
  final Color accentColor;

  const _WeeklyPerformanceChart({required this.accentColor});

  @override
  Widget build(BuildContext context) {
    const spots = [
      FlSpot(0, 35),
      FlSpot(1, 48),
      FlSpot(2, 42),
      FlSpot(3, 55),
      FlSpot(4, 50),
      FlSpot(5, 68),
      FlSpot(6, 72),
    ];
    const days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];

    return LineChart(
      LineChartData(
        backgroundColor: Colors.transparent,
        minY: 0,
        maxY: 100,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: 25,
          getDrawingHorizontalLine: (_) => FlLine(
            color: AppColors.borderSubtle,
            strokeWidth: 0.5,
          ),
        ),
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              interval: 25,
              getTitlesWidget: (value, meta) => Text(
                '${value.toInt()}',
                style: const TextStyle(fontSize: 8, color: AppColors.textLabel),
              ),
            ),
          ),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 22,
              getTitlesWidget: (value, meta) {
                final i = value.toInt();
                if (i < 0 || i >= days.length) return const SizedBox();
                return Text(
                  days[i],
                  style: TextStyle(
                    fontSize: 9,
                    color: i == days.length - 1 ? accentColor : AppColors.textLabel,
                    fontWeight: i == days.length - 1 ? FontWeight.w600 : FontWeight.normal,
                  ),
                );
              },
            ),
          ),
        ),
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) => touchedSpots.map((spot) {
              return LineTooltipItem(
                '${spot.y.toInt()} rep',
                TextStyle(color: accentColor, fontWeight: FontWeight.w600, fontSize: 11),
              );
            }).toList(),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            curveSmoothness: 0.3,
            color: accentColor,
            barWidth: 2.5,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, _, __, index) => FlDotCirclePainter(
                radius: index == spots.length - 1 ? 5 : 3,
                color: accentColor,
                strokeWidth: index == spots.length - 1 ? 2.5 : 0,
                strokeColor: AppColors.bgSurface2,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  accentColor.withOpacity(0.25),
                  accentColor.withOpacity(0),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
