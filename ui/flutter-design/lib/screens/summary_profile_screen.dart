import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
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
          padding: const EdgeInsets.all(16),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.bgSurface2,
              borderRadius: AppRadius.xl_,
              border: Border.all(color: AppColors.borderModal),
            ),
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Trophy
                Container(
                  width: 36, height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A1500),
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.brandGold),
                  ),
                  child: const Icon(Icons.emoji_events, color: AppColors.brandGold, size: 16),
                ),
                const SizedBox(height: 8),

                // Title
                Text('Antrenman Tamamlandı', style: AppTypography.displayMd),
                const SizedBox(height: 14),

                // Stats row
                Row(
                  children: [
                    Expanded(child: _StatCard(value: '${result.reps}', label: 'Tekrar', color: AppColors.brandGreen)),
                    const SizedBox(width: 8),
                    Expanded(child: _StatCard(value: '${result.xp}', label: 'XP', color: AppColors.brandGold)),
                    const SizedBox(width: 8),
                    Expanded(child: _StatCard(value: result.speed.toStringAsFixed(1), label: 'rep/sn', color: AppColors.brandBlue)),
                  ],
                ),
                const SizedBox(height: 14),

                // Feedback
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
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
                        style: AppTypography.labelXs.copyWith(
                          color: AppColors.brandGreen,
                          letterSpacing: 1.5,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(result.feedback, style: AppTypography.labelSm.copyWith(color: AppColors.textSecondary)),
                    ],
                  ),
                ),
                const SizedBox(height: 12),

                // CTA button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: onSave,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.brandGreen,
                      foregroundColor: AppColors.bgBase,
                      shape: RoundedRectangleBorder(borderRadius: AppRadius.md_),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      elevation: 0,
                    ),
                    child: Text(
                      'Profile Kaydet & Devam Et',
                      style: AppTypography.bodyMd.copyWith(
                        color: AppColors.bgBase,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.5,
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
    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
    decoration: BoxDecoration(
      color: AppColors.bgSurface3,
      borderRadius: AppRadius.md_,
    ),
    child: Column(
      children: [
        Text(value, style: AppTypography.statValue.copyWith(color: color)),
        const SizedBox(height: 2),
        Text(label.toUpperCase(), style: AppTypography.labelXs),
      ],
    ),
  );
}

// ════════════════════════════════════════════════════════════
//  EKRAN 4 — Profil & Lig Geçmişi (Profile Screen)
// ════════════════════════════════════════════════════════════

enum ActivityType { pushup, squat, other }

class ActivityItem {
  final String label;
  final ActivityType type;
  final String day;
  final String duration;
  final int accuracy;

  const ActivityItem({
    required this.label,
    required this.type,
    required this.day,
    required this.duration,
    required this.accuracy,
  });
}

extension ActivityColor on ActivityType {
  Color get color {
    switch (this) {
      case ActivityType.pushup: return AppColors.brandGreen;
      case ActivityType.squat:  return AppColors.brandBlue;
      case ActivityType.other:  return AppColors.brandPurple;
    }
  }
}

class ProfileScreen extends StatelessWidget {
  final String userName;
  final String leagueName;
  final List<double> chartData; // 7 values (normalized 0–100)
  final List<ActivityItem> activities;

  const ProfileScreen({
    super.key,
    this.userName = 'Pro-Developer',
    this.leagueName = 'Gümüş Lig',
    this.chartData = const [38, 52, 62, 48, 72, 82, 90],
    this.activities = const [
      ActivityItem(label: '50 Şınav', type: ActivityType.pushup, day: 'Dün', duration: '01:45 dk', accuracy: 92),
      ActivityItem(label: '30 Squat', type: ActivityType.squat, day: 'Pazartesi', duration: '02:10 dk', accuracy: 85),
      ActivityItem(label: '42 Şınav', type: ActivityType.other, day: 'Pazar', duration: '01:28 dk', accuracy: 88),
    ],
  });

  String get _initials => userName.length >= 2 ? userName.substring(0, 2).toUpperCase() : userName.toUpperCase();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgBase,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Notch
            Center(
              child: Container(
                width: 60, height: 6,
                margin: const EdgeInsets.only(top: 8, bottom: 4),
                decoration: BoxDecoration(
                  color: AppColors.bgSurface3,
                  borderRadius: AppRadius.sm_,
                ),
              ),
            ),

            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  // Avatar
                  Container(
                    width: 40, height: 40,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [AppColors.brandGreen, Color(0xFF1ABC9C)],
                      ),
                    ),
                    child: Center(
                      child: Text(
                        _initials,
                        style: const TextStyle(
                          color: AppColors.bgBase,
                          fontWeight: FontWeight.w700,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(userName, style: AppTypography.cardName),
                      const SizedBox(height: 2),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.bgSurface3,
                          borderRadius: AppRadius.sm_,
                          border: Border.all(color: AppColors.borderPurple),
                        ),
                        child: Text(
                          leagueName.toUpperCase(),
                          style: AppTypography.labelXs.copyWith(
                            color: AppColors.brandPurple,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Chart section
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('SON 7 GÜN — ŞINAV', style: AppTypography.labelXs.copyWith(color: AppColors.textDimmed)),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 90,
                    child: _WeeklyLineChart(data: chartData),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 12),

            // Activity list
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text('AKTİVİTE GEÇMİŞİ', style: AppTypography.labelXs.copyWith(color: AppColors.textDimmed)),
            ),
            const SizedBox(height: 4),
            ...activities.map((a) => _ActivityRow(item: a)),
          ],
        ),
      ),
    );
  }
}

// ── Weekly Line Chart (fl_chart) ──────────────────────────────
class _WeeklyLineChart extends StatelessWidget {
  final List<double> data;

  const _WeeklyLineChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final spots = List.generate(
      data.length,
      (i) => FlSpot(i.toDouble(), data[i]),
    );
    const days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Dün'];

    return LineChart(
      LineChartData(
        backgroundColor: Colors.transparent,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: 33,
          getDrawingHorizontalLine: (_) => FlLine(
            color: AppColors.borderSubtle,
            strokeWidth: 1,
          ),
        ),
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 18,
              getTitlesWidget: (value, meta) {
                final i = value.toInt();
                if (i < 0 || i >= days.length) return const SizedBox();
                return Text(
                  days[i],
                  style: TextStyle(
                    fontSize: 7,
                    color: i == days.length - 1 ? AppColors.brandGreen : AppColors.textLabel,
                  ),
                );
              },
            ),
          ),
        ),
        lineTouchData: const LineTouchData(enabled: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: AppColors.brandGreen,
            barWidth: 2,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, _, __, index) => FlDotCirclePainter(
                radius: index == spots.length - 1 ? 4 : 3,
                color: AppColors.brandGreen,
                strokeWidth: index == spots.length - 1 ? 2 : 0,
                strokeColor: AppColors.bgSurface1,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  AppColors.brandGreen.withOpacity(0.3),
                  AppColors.brandGreen.withOpacity(0),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Activity Row ──────────────────────────────────────────────
class _ActivityRow extends StatelessWidget {
  final ActivityItem item;

  const _ActivityRow({required this.item});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
    decoration: const BoxDecoration(
      border: Border(bottom: BorderSide(color: AppColors.borderSubtle)),
    ),
    child: Row(
      children: [
        // Dot
        Container(
          width: 6, height: 6,
          margin: const EdgeInsets.only(right: 10),
          decoration: BoxDecoration(
            color: item.type.color,
            shape: BoxShape.circle,
          ),
        ),
        // Info
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.label, style: AppTypography.activityTitle),
              const SizedBox(height: 1),
              Text('${item.day} · ${item.duration}', style: AppTypography.activityMeta),
            ],
          ),
        ),
        // Accuracy
        Text(
          '%${item.accuracy}',
          style: AppTypography.bodyMd.copyWith(
            color: item.type.color,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    ),
  );
}
