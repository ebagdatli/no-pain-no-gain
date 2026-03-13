import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';
import '../providers/workout_provider.dart';
import '../theme/app_theme.dart';

// ════════════════════════════════════════════════════════════
//  EKRAN 2 — Canlı Takip (Live Tracking Screen)
// ════════════════════════════════════════════════════════════

class LiveTrackingScreen extends ConsumerStatefulWidget {
  final int? repCount;
  final double? accuracy;
  final VoidCallback? onStop;

  const LiveTrackingScreen({
    super.key,
    this.repCount,
    this.accuracy,
    this.onStop,
  });

  @override
  ConsumerState<LiveTrackingScreen> createState() => _LiveTrackingScreenState();
}

class _LiveTrackingScreenState extends ConsumerState<LiveTrackingScreen> {
  CameraController? _cameraController;
  final PoseDetector _poseDetector = PoseDetector(options: PoseDetectorOptions());
  List<PoseLandmark>? _landmarks;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) return;
      
      final frontCamera = cameras.firstWhere(
        (cam) => cam.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        frontCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      
      await _cameraController?.initialize();
      if (mounted) setState(() {});
    } catch (e) {
      debugPrint('Camera init error: $e');
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    _poseDetector.close();
    super.dispose();
  }

  bool _isWarning(double acc) => acc < 80;

  Color _barColor(double acc) => _isWarning(acc) ? AppColors.brandOrange : AppColors.brandGreen;

  @override
  Widget build(BuildContext context) {
    // Read from Riverpod state or use mock values passed from constructor
    final workoutState = ref.watch(workoutNotifierProvider);
    final currentRepCount = widget.repCount ?? workoutState.repCount;
    final currentAccuracy = widget.accuracy ?? workoutState.accuracy;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Camera BG (Actual Camera or Mock) ──
          if (_cameraController != null && _cameraController!.value.isInitialized)
            _CameraBackground(controller: _cameraController!)
          else
            _MockCameraBackground(),

          // ── Grid overlay ──────────────────────────────────────────
          _GridOverlay(),

          // ── Skeleton overlay ──────────────────────────────────────
          Center(
            child: SizedBox(
              width: 100,
              height: 220,
              child: CustomPaint(
                painter: _FullSkeletonPainter(landmarks: _landmarks?.cast<PoseLandmark>()),
              ),
            ),
          ),

          // ── Top notch ─────────────────────────────────────────────
          Positioned(
            top: 10, left: 0, right: 0,
            child: Center(
              child: Container(
                width: 60, height: 6,
                decoration: BoxDecoration(
                  color: AppColors.bgSurface3,
                  borderRadius: AppRadius.sm_,
                ),
              ),
            ),
          ),

          // ── Rep counter (top right) ───────────────────────────────
          Positioned(
            top: 16, right: 16,
            child: Text(
              '$currentRepCount',
              style: AppTypography.counter,
            ),
          ),

          // ── Accuracy bar (left side) ──────────────────────────────
          Positioned(
            left: 12,
            top: 0, bottom: 0,
            child: Center(
              child: _AccuracyBar(
                accuracy: currentAccuracy,
                barColor: _barColor(currentAccuracy),
                pctColor: _barColor(currentAccuracy),
              ),
            ),
          ),

          // ── Bottom bar with stop button ───────────────────────────
          Positioned(
            bottom: 0, left: 0, right: 0,
            child: _BottomBar(onStop: widget.onStop),
          ),
        ],
      ),
    );
  }
}

// ── Camera Background (Real) ──────────────────────────────────
class _CameraBackground extends StatelessWidget {
  final CameraController controller;
  
  const _CameraBackground({required this.controller});

  @override
  Widget build(BuildContext context) {
    return SizedBox.expand(
      child: FittedBox(
        fit: BoxFit.cover,
        child: SizedBox(
          width: controller.value.previewSize?.height ?? 1,
          height: controller.value.previewSize?.width ?? 1,
          child: CameraPreview(controller),
        ),
      ),
    );
  }
}

// ── Mock Camera Background (Fallback when camera not ready) ───
class _MockCameraBackground extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
    decoration: const BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFF0A1A0A), Color(0xFF050D05)],
      ),
    ),
  );
}

// ── Grid Overlay ──────────────────────────────────────────────
class _GridOverlay extends StatelessWidget {
  @override
  Widget build(BuildContext context) => CustomPaint(
    painter: _GridPainter(),
    child: const SizedBox.expand(),
  );
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.gridLine
      ..strokeWidth = 1;
    const step = 24.0;
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }
  @override
  bool shouldRepaint(_) => false;
}

// ── Full Skeleton Painter (ML Kit aware) ──────────────────────
class _FullSkeletonPainter extends CustomPainter {
  final List<PoseLandmark>? landmarks;

  _FullSkeletonPainter({this.landmarks});

  @override
  void paint(Canvas canvas, Size size) {
    final sx = size.width / 100;
    final sy = size.height / 220;
    Offset p(double x, double y) => Offset(x * sx, y * sy);

    void line(Offset a, Offset b, {double opacity = 1.0, double width = 1.5}) {
      canvas.drawLine(a, b, Paint()
        ..color = AppColors.brandGreen.withOpacity(opacity)
        ..strokeWidth = width
        ..strokeCap = StrokeCap.round);
    }

    void joint(Offset pt, {double r = 3.5, double opacity = 0.8}) {
      canvas.drawCircle(pt, r, Paint()
        ..color = AppColors.brandGreen.withOpacity(opacity)
        ..style = PaintingStyle.fill);
    }
    
    // Fallback drawing logic if no ML Kit landmarks detected (default skeletal view)
    if (landmarks == null || landmarks!.isEmpty) {
      // Head
      canvas.drawCircle(p(50, 18), 10 * sx, Paint()..color = AppColors.brandGreen.withOpacity(0.06)..style = PaintingStyle.fill);
      canvas.drawCircle(p(50, 18), 10 * sx, Paint()..color = AppColors.brandGreen..strokeWidth = 1.5..style = PaintingStyle.stroke);

      // Neck & spine
      line(p(50, 28), p(50, 44));
      line(p(50, 44), p(50, 118), width: 2.0);

      // Shoulders
      line(p(50, 44), p(22, 66), width: 2.0);
      line(p(50, 44), p(78, 66), width: 2.0);

      // Arms
      line(p(22, 66), p(10, 104), opacity: 0.9);
      line(p(10, 104), p(4, 138), opacity: 0.7);
      line(p(78, 66), p(90, 104), opacity: 0.9);
      line(p(90, 104), p(96, 138), opacity: 0.7);

      // Hips
      line(p(50, 118), p(32, 128), width: 2.0);
      line(p(50, 118), p(68, 128), width: 2.0);

      // Legs
      line(p(32, 128), p(28, 170), opacity: 0.9);
      line(p(28, 170), p(26, 212), opacity: 0.7);
      line(p(68, 128), p(72, 170), opacity: 0.9);
      line(p(72, 170), p(74, 212), opacity: 0.7);

      // Joints
      for (final pt in [p(22, 66), p(78, 66), p(32, 128), p(68, 128)]) {
        joint(pt, r: 3.5 * sx);
      }
      for (final pt in [p(10, 104), p(90, 104), p(28, 170), p(72, 170)]) {
        joint(pt, r: 2.5 * sx, opacity: 0.7);
      }
    } else {
      // Draw actual ML Kit landmarks
      // Currently using a simplified approach
      for (final landmark in landmarks!) {
        joint(Offset(landmark.x, landmark.y), r: 4.0, opacity: 0.9);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _FullSkeletonPainter oldDelegate) {
    return oldDelegate.landmarks != landmarks;
  }
}

// ── Accuracy Bar ──────────────────────────────────────────────
class _AccuracyBar extends StatelessWidget {
  final double accuracy;
  final Color barColor;
  final Color pctColor;

  const _AccuracyBar({
    required this.accuracy,
    required this.barColor,
    required this.pctColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '${accuracy.round()}%',
          style: AppTypography.bodyMd.copyWith(
            color: pctColor,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        // Track
        Container(
          width: 8,
          height: 120,
          decoration: BoxDecoration(
            color: AppColors.bgSurface3,
            borderRadius: AppRadius.sm_,
          ),
          child: Align(
            alignment: Alignment.bottomCenter,
            child: AnimatedContainer(
               duration: const Duration(milliseconds: 500),
              curve: Curves.easeOut,
              width: 8,
              height: 120 * (accuracy / 100),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [barColor, barColor.withOpacity(0.7)],
                ),
                borderRadius: AppRadius.sm_,
              ),
            ),
          ),
        ),
        const SizedBox(height: 4),
        RotatedBox(
          quarterTurns: 3,
          child: Text(
            'ACCURACY',
            style: AppTypography.labelXs.copyWith(
              color: AppColors.textMuted,
              letterSpacing: 1.5,
            ),
          ),
        ),
      ],
    );
  }
}

// ── Bottom Bar ────────────────────────────────────────────────
class _BottomBar extends StatelessWidget {
  final VoidCallback? onStop;

  const _BottomBar({this.onStop});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 72,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.transparent, Color(0xCC000000)],
        ),
      ),
      child: Center(
        child: _StopButton(onTap: onStop),
      ),
    );
  }
}

// ── Stop Button ───────────────────────────────────────────────
class _StopButton extends StatelessWidget {
  final VoidCallback? onTap;

  const _StopButton({this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: AppColors.brandRed,
          shape: BoxShape.circle,
          border: Border.all(color: const Color(0xFFFF6B6B), width: 3),
          boxShadow: [
            BoxShadow(
              color: AppColors.brandRedGlow,
              blurRadius: 16,
              spreadRadius: 0,
            ),
          ],
        ),
        child: const Icon(Icons.stop_rounded, color: Colors.white, size: 20),
      ),
    );
  }
}
