import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'workout_provider.g.dart';

class WorkoutState {
  final int repCount;
  final double accuracy;

  const WorkoutState({
    required this.repCount,
    required this.accuracy,
  });

  WorkoutState copyWith({
    int? repCount,
    double? accuracy,
  }) {
    return WorkoutState(
      repCount: repCount ?? this.repCount,
      accuracy: accuracy ?? this.accuracy,
    );
  }
}

@riverpod
class WorkoutNotifier extends _$WorkoutNotifier {
  @override
  WorkoutState build() => const WorkoutState(repCount: 0, accuracy: 100.0);

  void incrementRep() {
    state = state.copyWith(repCount: state.repCount + 1);
  }

  void updateAccuracy(double acc) {
    state = state.copyWith(accuracy: acc);
  }
}
