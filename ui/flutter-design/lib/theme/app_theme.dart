import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// ════════════════════════════════════════════════════════════
//  FITNESS AI — Design Tokens
//  Tüm renk, tipografi ve spacing değerleri burada tanımlı.
//  Kullanım: AppColors.brandGreen, AppTypography.counter, AppSpacing.md
// ════════════════════════════════════════════════════════════

// ── Colors ──────────────────────────────────────────────────
abstract class AppColors {
  // Brand
  static const brandGreen     = Color(0xFF2ECC71);
  static const brandGreenDim  = Color(0xFF1AAD5E);
  static const brandGreenGlow = Color(0x262ECC71); // ~15% opacity
  static const brandBlue      = Color(0xFF3498DB);
  static const brandBlueDim   = Color(0x1A3498DB); // ~10% opacity
  static const brandOrange    = Color(0xFFE67E22);
  static const brandRed       = Color(0xFFE74C3C);
  static const brandRedGlow   = Color(0x80E74C3C); // ~50% opacity
  static const brandGold      = Color(0xFFF39C12);
  static const brandPurple    = Color(0xFF9B9BFF);
  static const brandPurpleDim = Color(0x269B9BFF); // ~15% opacity

  // Backgrounds
  static const bgBase         = Color(0xFF0A0A0A);
  static const bgSurface1     = Color(0xFF0D0D0D);
  static const bgSurface2     = Color(0xFF141414);
  static const bgSurface3     = Color(0xFF1A1A1A);
  static const bgCardGreen    = Color(0xFF0F1F14);
  static const bgCardBlue     = Color(0xFF0F1720);
  static const bgCardFeedback = Color(0xFF0F1A12);
  static const bgOverlay      = Color(0xBF000000); // 75% black

  // Borders
  static const borderDefault  = Color(0xFF222222);
  static const borderSubtle   = Color(0xFF1A1A1A);
  static const borderGreen    = Color(0xFF1A4D28);
  static const borderBlue     = Color(0xFF1A3A50);
  static const borderPurple   = Color(0xFF3A3A60);
  static const borderFeedback = Color(0xFF1A3D22);
  static const borderModal    = Color(0xFF252525);

  // Text
  static const textPrimary    = Color(0xFFFFFFFF);
  static const textSecondary  = Color(0xFFAAAAAA);
  static const textMuted      = Color(0xFF666666);
  static const textDimmed     = Color(0xFF555555);
  static const textLabel      = Color(0xFF444444);

  // Grid overlay for camera screen
  static const gridLine       = Color(0x0A2ECC71); // ~4% green
}

// ── Typography ───────────────────────────────────────────────
abstract class AppTypography {
  // Display font: Bebas Neue (loaded via pubspec assets)
  // Body font: DM Sans (loaded via google_fonts)

  static TextStyle get counter => const TextStyle(
    fontFamily: 'BebasNeue',
    fontSize: 64,
    height: 1.0,
    color: AppColors.brandGreen,
    shadows: [Shadow(color: Color(0x662ECC71), blurRadius: 20)],
  );

  static TextStyle get displayLg => const TextStyle(
    fontFamily: 'BebasNeue',
    fontSize: 80,
    height: 1.0,
    color: AppColors.textPrimary,
  );

  static TextStyle get displayMd => const TextStyle(
    fontFamily: 'BebasNeue',
    fontSize: 20,
    height: 1.2,
    color: AppColors.textPrimary,
  );

  static TextStyle get displaySm => const TextStyle(
    fontFamily: 'BebasNeue',
    fontSize: 18,
    height: 1.2,
    color: AppColors.textPrimary,
  );

  static TextStyle get cardName => GoogleFonts.dmSans(
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
  );

  static TextStyle get body => GoogleFonts.dmSans(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    color: AppColors.textPrimary,
  );

  static TextStyle get bodyMd => GoogleFonts.dmSans(
    fontSize: 11,
    fontWeight: FontWeight.w500,
    color: AppColors.textPrimary,
  );

  static TextStyle get labelSm => GoogleFonts.dmSans(
    fontSize: 9,
    fontWeight: FontWeight.w500,
    letterSpacing: 1.5,
    color: AppColors.textMuted,
  );

  static TextStyle get labelXs => GoogleFonts.dmSans(
    fontSize: 8,
    fontWeight: FontWeight.w400,
    letterSpacing: 2.0,
    color: AppColors.textMuted,
  );

  static TextStyle get statValue => const TextStyle(
    fontFamily: 'BebasNeue',
    fontSize: 20,
    height: 1.0,
  );

  static TextStyle get activityTitle => GoogleFonts.dmSans(
    fontSize: 11,
    fontWeight: FontWeight.w500,
    color: const Color(0xFFDDDDDD),
  );

  static TextStyle get activityMeta => GoogleFonts.dmSans(
    fontSize: 9,
    color: AppColors.textDimmed,
  );
}

// ── Spacing ──────────────────────────────────────────────────
abstract class AppSpacing {
  static const double xs   = 4.0;
  static const double sm   = 8.0;
  static const double md   = 12.0;
  static const double lg   = 16.0;
  static const double xl   = 20.0;
  static const double xxl  = 24.0;
  static const double xxxl = 32.0;
}

// ── Border Radius ─────────────────────────────────────────────
abstract class AppRadius {
  static const double sm    = 6.0;
  static const double md    = 10.0;
  static const double lg    = 14.0;
  static const double xl    = 20.0;
  static const double xxl   = 32.0;

  static const sm_  = BorderRadius.all(Radius.circular(sm));
  static const md_  = BorderRadius.all(Radius.circular(md));
  static const lg_  = BorderRadius.all(Radius.circular(lg));
  static const xl_  = BorderRadius.all(Radius.circular(xl));
  static const xxl_ = BorderRadius.all(Radius.circular(xxl));
}

// ── Phone dimensions (for preview/test) ──────────────────────
abstract class AppPhoneFrame {
  static const double width  = 260.0;
  static const double height = 520.0;
  static const double radius = AppRadius.xxl;
}

// ── ThemeData ─────────────────────────────────────────────────
final appTheme = ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: AppColors.bgBase,
  colorScheme: const ColorScheme.dark(
    primary:   AppColors.brandGreen,
    secondary: AppColors.brandBlue,
    error:     AppColors.brandRed,
    surface:   AppColors.bgSurface2,
  ),
  textTheme: GoogleFonts.dmSansTextTheme(ThemeData.dark().textTheme),
  useMaterial3: true,
);
