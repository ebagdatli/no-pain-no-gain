import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'theme/app_theme.dart';
import 'screens/landing_screen.dart';
import 'screens/live_tracking_screen.dart';
import 'screens/summary_profile_screen.dart';

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
              onStop: () => context.go('/summary'),
            );
          },
        ),
        GoRoute(
          path: '/summary',
          builder: (context, state) => Stack(
            children: [
              const LiveTrackingScreen(repCount: 42, accuracy: 92),
              SummaryModal(
                result: const WorkoutResult(
                  reps: 42,
                  xp: 850,
                  speed: 1.2,
                  feedback: 'Sırtın biraz fazla kavisliydi. Bir sonraki antrenmanda belini düz tutmaya odaklan.',
                ),
                onSave: () => context.go('/profile'),
              ),
            ],
          ),
        ),
        GoRoute(
          path: '/profile',
          builder: (context, state) => const ProfileScreen(),
        ),
      ],
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
      // SafeArea to avoid overlapping on certain devices if needed
      bottomNavigationBar: _buildBottomBar(context),
    );
  }

  Widget _buildBottomBar(BuildContext context) {
    // Current URI to determine the active tab
    final String location = GoRouterState.of(context).uri.toString();
    int currentIndex = _calculateSelectedIndex(location);

    return BottomNavigationBar(
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
          icon: Icon(Icons.analytics_outlined),
          activeIcon: Icon(Icons.analytics),
          label: 'Özet',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline),
          activeIcon: Icon(Icons.person),
          label: 'Profil',
        ),
      ],
    );
  }

  static int _calculateSelectedIndex(String location) {
    if (location.startsWith('/tracking')) {
      return 1;
    }
    if (location.startsWith('/summary')) {
      return 2;
    }
    if (location.startsWith('/profile')) {
      return 3;
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
        context.go('/summary');
        break;
      case 3:
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
