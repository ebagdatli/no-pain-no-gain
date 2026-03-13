import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

// ════════════════════════════════════════════════════════════
//  EKRAN 1 — Karşılama (Landing Screen)
// ════════════════════════════════════════════════════════════

enum ExerciseType { pushup, squat }

class LandingScreen extends StatelessWidget {
  final void Function(ExerciseType type)? onSelectExercise;

  const LandingScreen({super.key, this.onSelectExercise});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0D0D0D), Color(0xFF111820)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // Notch sim
              const _Notch(),
              const SizedBox(height: 8),

              // Neon skeleton figure
              const SizedBox(
                width: 100,
                height: 160,
                child: _SkeletonFigure(),
              ),

              const SizedBox(height: 4),

              // Sub-tagline
              Text(
                'YAPAY ZEKA ANTRENÖRÜN',
                style: AppTypography.labelXs.copyWith(
                  color: const Color(0xFF888888),
                  letterSpacing: 3,
                ),
              ),

              const SizedBox(height: 2),

              // Main title
              const Text(
                'Cebinde.',
                style: TextStyle(
                  fontFamily: 'BebasNeue',
                  fontSize: 28,
                  color: AppColors.textPrimary,
                  height: 1.2,
                ),
              ),

              const SizedBox(height: 16),

              // Exercise cards
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  children: [
                    _ExerciseCard(
                      label: 'Analiz',
                      name: 'Şınav Analizi',
                      variant: ExerciseType.pushup,
                      icon: _ArrowUpDownIcon(),
                      onTap: () => onSelectExercise?.call(ExerciseType.pushup),
                    ),
                    const SizedBox(height: 10),
                    _ExerciseCard(
                      label: 'Analiz',
                      name: 'Squat Analizi',
                      variant: ExerciseType.squat,
                      icon: _SquatIcon(),
                      onTap: () => onSelectExercise?.call(ExerciseType.squat),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Sub-widget: Exercise Card ─────────────────────────────────
class _ExerciseCard extends StatelessWidget {
  final String label;
  final String name;
  final ExerciseType variant;
  final Widget icon;
  final VoidCallback? onTap;

  const _ExerciseCard({
    required this.label,
    required this.name,
    required this.variant,
    required this.icon,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isPushup = variant == ExerciseType.pushup;
    final bg = isPushup ? AppColors.bgCardGreen : AppColors.bgCardBlue;
    final border = isPushup ? AppColors.borderGreen : AppColors.borderBlue;
    final accentColor = isPushup ? AppColors.brandGreen : AppColors.brandBlue;
    final iconBg = isPushup ? AppColors.brandGreenGlow : AppColors.brandBlueDim;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: AppRadius.lg_,
          border: Border.all(color: border),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label.toUpperCase(),
                  style: AppTypography.labelXs.copyWith(
                    color: accentColor,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 2),
                Text(name, style: AppTypography.cardName),
              ],
            ),
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: iconBg,
                shape: BoxShape.circle,
              ),
              child: Center(child: icon),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Neon Skeleton Figure (CustomPainter) ──────────────────────
class _SkeletonFigure extends StatelessWidget {
  const _SkeletonFigure();

  @override
  Widget build(BuildContext context) => CustomPaint(
    painter: _SkeletonPainter(),
  );
}

class _SkeletonPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final sx = size.width / 100;
    final sy = size.height / 160;
    Offset p(double x, double y) => Offset(x * sx, y * sy);

    final paint = Paint()
      ..color = AppColors.brandGreen
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final dimPaint = Paint()
      ..color = AppColors.brandGreen.withOpacity(0.5)
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final jointPaint = Paint()
      ..color = AppColors.brandGreen.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    // Head
    canvas.drawCircle(p(50, 14), 8 * sx, paint..color = AppColors.brandGreen.withOpacity(0.7));

    // Spine
    canvas.drawLine(p(50, 22), p(50, 85), paint..color = AppColors.brandGreen.withOpacity(0.9));

    // Shoulders
    canvas.drawLine(p(50, 32), p(28, 50), paint..color = AppColors.brandGreen.withOpacity(0.8));
    canvas.drawLine(p(50, 32), p(72, 50), paint..color = AppColors.brandGreen.withOpacity(0.8));

    // Arms
    canvas.drawLine(p(28, 50), p(18, 78), dimPaint..color = AppColors.brandGreen.withOpacity(0.7));
    canvas.drawLine(p(18, 78), p(12, 102), dimPaint..color = AppColors.brandGreen.withOpacity(0.5));
    canvas.drawLine(p(72, 50), p(82, 78), dimPaint..color = AppColors.brandGreen.withOpacity(0.7));
    canvas.drawLine(p(82, 78), p(88, 102), dimPaint..color = AppColors.brandGreen.withOpacity(0.5));

    // Hips
    canvas.drawLine(p(50, 85), p(34, 92), paint..color = AppColors.brandGreen.withOpacity(0.8));
    canvas.drawLine(p(50, 85), p(66, 92), paint..color = AppColors.brandGreen.withOpacity(0.8));

    // Legs
    canvas.drawLine(p(34, 92), p(30, 120), dimPaint..color = AppColors.brandGreen.withOpacity(0.7));
    canvas.drawLine(p(30, 120), p(28, 150), dimPaint..color = AppColors.brandGreen.withOpacity(0.5));
    canvas.drawLine(p(66, 92), p(70, 120), dimPaint..color = AppColors.brandGreen.withOpacity(0.7));
    canvas.drawLine(p(70, 120), p(72, 150), dimPaint..color = AppColors.brandGreen.withOpacity(0.5));

    // Major joints
    for (final pt in [p(28, 50), p(72, 50), p(34, 92), p(66, 92)]) {
      canvas.drawCircle(pt, 2.5 * sx, jointPaint);
    }
    // Minor joints
    for (final pt in [p(18, 78), p(82, 78), p(30, 120), p(70, 120)]) {
      canvas.drawCircle(pt, 2 * sx, jointPaint..color = AppColors.brandGreen.withOpacity(0.5));
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// ── Icon Widgets ──────────────────────────────────────────────
class _ArrowUpDownIcon extends StatelessWidget {
  @override
  Widget build(BuildContext context) => CustomPaint(
    size: const Size(18, 18),
    painter: _ArrowPainter(),
  );
}

class _ArrowPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = AppColors.brandGreen
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    final cx = size.width / 2;
    canvas.drawLine(Offset(cx, 0), Offset(cx, size.height), p);
    canvas.drawLine(Offset(cx - 4, 4), Offset(cx, 0), p);
    canvas.drawLine(Offset(cx + 4, 4), Offset(cx, 0), p);
    canvas.drawLine(Offset(cx - 4, size.height - 4), Offset(cx, size.height), p);
    canvas.drawLine(Offset(cx + 4, size.height - 4), Offset(cx, size.height), p);
  }
  @override
  bool shouldRepaint(_) => false;
}

class _SquatIcon extends StatelessWidget {
  @override
  Widget build(BuildContext context) => CustomPaint(
    size: const Size(18, 18),
    painter: _SquatPainter(),
  );
}

class _SquatPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = AppColors.brandBlue
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    final path = Path()
      ..moveTo(size.width * 0.25, 0)
      ..lineTo(size.width * 0.25, size.height * 0.5)
      ..quadraticBezierTo(
        size.width * 0.25, size.height * 0.83,
        size.width * 0.58, size.height * 0.83,
      );
    canvas.drawPath(path, p);
    // Arrow
    canvas.drawLine(Offset(size.width * 0.42, size.height * 0.5), Offset(size.width * 0.25, size.height * 0.67), p);
    canvas.drawLine(Offset(size.width * 0.08, size.height * 0.5), Offset(size.width * 0.25, size.height * 0.67), p);
    // Person head
    canvas.drawCircle(Offset(size.width * 0.67, size.height * 0.22), 2.5, p..style = PaintingStyle.fill..color = AppColors.brandBlue);
  }
  @override
  bool shouldRepaint(_) => false;
}

// ── Notch ─────────────────────────────────────────────────────
class _Notch extends StatelessWidget {
  const _Notch();

  @override
  Widget build(BuildContext context) => Container(
    width: 60,
    height: 6,
    margin: const EdgeInsets.only(top: 8),
    decoration: BoxDecoration(
      color: AppColors.borderDefault,
      borderRadius: AppRadius.sm_,
    ),
  );
}
