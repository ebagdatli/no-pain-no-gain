import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'theme/app_theme.dart';
import 'screens/landing_screen.dart';
import 'screens/live_tracking_screen.dart';
import 'screens/summary_profile_screen.dart';
import 'screens/activity_detail_screen.dart';

void main() {
  runApp(const ProviderScope(child: FitnessAiApp()));
}

// ── Router ────────────────────────────────────────────────────
final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<NavigatorState> _shellNavigatorKey = GlobalKey<NavigatorState>();

final _router = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/',
  routes: [
    ShellRoute(
      navigatorKey: _shellNavigatorKey,
      builder: (context, state, child) {
        return ScaffoldWithNavBar(child: child);
      },
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => LandingScreen(
            onSelectExercise: (type) => context.go('/tracking', extra: type),
          ),
        ),
        GoRoute(
          path: '/tracking',
          builder: (context, state) {
            final type = state.extra as ExerciseType? ?? ExerciseType.pushup;
            return LiveTrackingScreen(
              repCount: 12,
              accuracy: 78,
              onStop: () {
                // Task 1.2: Antrenman bitince ResultScreen modal olarak açılır
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  isDismissible: false,
                  enableDrag: false,
                  builder: (_) => SummaryModal(
                    result: const WorkoutResult(
                      reps: 42,
                      xp: 850,
                      speed: 1.2,
                      feedback:
                          'Sırtın biraz fazla kavisliydi. Bir sonraki antrenmanda belini düz tutmaya odaklan.',
                    ),
                    onSave: () {
                      Navigator.of(context).pop(); // Modal kapat
                      context.go('/profile'); // Profil sekmesine yönlendir
                    },
                  ),
                );
              },
            );
          },
        ),
        GoRoute(
          path: '/profile',
          builder: (context, state) => const ProfileScreen(),
        ),
      ],
    ),
    // Activity detail — full-screen route (shell dışı)
    GoRoute(
      path: '/activity-detail',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final session = state.extra as TrainingSession?;
        return ActivityDetailScreen(item: session);
      },
    ),
  ],
);

class ScaffoldWithNavBar extends StatelessWidget {
  final Widget child;

  const ScaffoldWithNavBar({
    required this.child,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: _buildBottomBar(context),
    );
  }

  // Task 1.1: 3 sekme — Ana Sayfa, Kamera, Profil (Özet kaldırıldı)
  Widget _buildBottomBar(BuildContext context) {
    final String location = GoRouterState.of(context).uri.toString();
    int currentIndex = _calculateSelectedIndex(location);

    return Container(
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: AppColors.borderSubtle, width: 0.5),
        ),
      ),
      child: BottomNavigationBar(
        backgroundColor: AppColors.bgSurface2,
        selectedItemColor: AppColors.brandGreen,
        unselectedItemColor: AppColors.textMuted,
        showUnselectedLabels: true,
        type: BottomNavigationBarType.fixed,
        currentIndex: currentIndex,
        onTap: (int index) => _onItemTapped(index, context),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: 'Ana Sayfa',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.camera_alt_outlined),
            activeIcon: Icon(Icons.camera_alt),
            label: 'Kamera',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: 'Profil',
          ),
        ],
      ),
    );
  }

  static int _calculateSelectedIndex(String location) {
    if (location.startsWith('/tracking')) {
      return 1;
    }
    if (location.startsWith('/profile')) {
      return 2;
    }
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        context.go('/');
        break;
      case 1:
        context.go('/tracking');
        break;
      case 2:
        context.go('/profile');
        break;
    }
  }
}

// ── App Root ──────────────────────────────────────────────────
class FitnessAiApp extends StatelessWidget {
  const FitnessAiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Fitness AI',
      theme: appTheme,
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }
}
