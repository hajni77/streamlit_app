import 'package:vid_app/common/app_export.dart';
import 'package:vid_app/provider/welcome_back_provider.dart';
import 'package:flutter/material.dart';
import 'package:vid_app/common/utils/validation_functions.dart';
import 'package:vid_app/common/ui/custom_text_form_field.dart';
import 'package:vid_app/common/ui/base_button.dart';
import 'package:vid_app/aws_auth.dart';
import 'package:vid_app/common/ui/app_bar.dart';

// ADD THIS IMPORT
import 'package:vid_app/services/bathroom_api_auth_service.dart';

/// WelcomeBackScreen UI with Bathroom API Integration
/// 
/// Changes made:
/// 1. Added BathroomApiAuthService integration
/// 2. Login now authenticates with both AWS Cognito and Bathroom API
/// 3. Bathroom API authentication happens automatically after AWS login

class WelcomeBackScreen extends ConsumerStatefulWidget {
  const WelcomeBackScreen({Key? key}) : super(key: key);

  @override
  WelcomeBackScreenState createState() => WelcomeBackScreenState();

  static Widget builder(BuildContext context) {
    return ProviderScope(
      child: WelcomeBackScreen(),
    );
  }
}

class WelcomeBackScreenState extends ConsumerState<WelcomeBackScreen> {
  GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final AwsAuth _awsAuth = AwsAuth();
  
  // ADD THIS: Bathroom API service
  final BathroomApiAuthService _bathroomApi = BathroomApiAuthService();
  
  // ADD THIS: Loading state for bathroom API
  bool _isSyncingBathroomApi = false;
  
  @override
  void initState() {
    super.initState();
    // ADD THIS: Initialize bathroom API service
    _bathroomApi.init();
  }

  @override
  Widget build(BuildContext context) {
    final welcomeBackState = ref.watch(welcomeBackProvider);
    final welcomeBackNotifier = ref.watch(welcomeBackProvider.notifier);
    
    return SafeArea(
      child: Scaffold(
        backgroundColor: theme.colorScheme.background,
        resizeToAvoidBottomInset: false,
        appBar: buildAppBar(context),
        body: SizedBox(
          child: Container(
            child: SizedBox(
              height: SizeUtils.height,
              child: Form(
                key: _formKey,
                child: Container(
                  width: 390.h,
                  padding: EdgeInsets.symmetric(vertical: 16.v),
                  child: Column(
                    children: [
                      Container(
                        decoration: AppDecoration.outlineBlackF,
                        child: Text(
                          "lbl_welcome_back".tr,
                          style: CustomTextStyles.headlineLargeFiraSans,
                        ),
                      ),
                      SizedBox(height: 18.v),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Padding(
                          padding: EdgeInsets.only(left: 32.h),
                          child: Text(
                            "lbl_email".tr,
                            style: theme.textTheme.titleSmall,
                          ),
                        ),
                      ),
                      SizedBox(height: 6.v),
                      Padding(
                        padding: EdgeInsets.symmetric(horizontal: 10.h),
                        child: CustomTextFormField(
                          controller: welcomeBackState.emailController,
                          hintText: "msg_example_gmail_com".tr,
                          hintStyle: theme.textTheme.bodyMedium,
                          textInputType: TextInputType.emailAddress,
                          textStyle: theme.textTheme.titleMedium,
                          validator: (value) {
                            if (value == null ||
                                (!isValidEmail(value, isRequired: true))) {
                              return "err_msg_please_enter_valid_email".tr;
                            }
                            return null;
                          },
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 20.h,
                            vertical: 16.v,
                          ),
                        ),
                      ),
                      SizedBox(height: 18.v),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Padding(
                          padding: EdgeInsets.only(left: 32.h),
                          child: Text(
                            "lbl_password".tr,
                            style: theme.textTheme.titleSmall,
                          ),
                        ),
                      ),
                      SizedBox(height: 6.v),
                      Padding(
                        padding: EdgeInsets.symmetric(horizontal: 10.h),
                        child: CustomTextFormField(
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 20.h,
                            vertical: 16.v,
                          ),
                          controller: welcomeBackState.passwordController,
                          hintText: "password".tr,
                          hintStyle: theme.textTheme.bodyMedium,
                          textInputAction: TextInputAction.done,
                          textInputType: TextInputType.visiblePassword,
                          textStyle: theme.textTheme.titleMedium,
                          suffix: InkWell(
                            onTap: () {
                              welcomeBackNotifier.changePasswordVisibility();
                            },
                            child: Container(
                              margin:
                                  EdgeInsets.fromLTRB(17.h, 16.v, 17.h, 16.v),
                              child: CustomImageView(
                                imagePath: welcomeBackState.isShowPassword
                                    ? ImageConstant.imgWhiteVisibleVector
                                    : ImageConstant.imgWhitenotVisibleVector,
                                height: 24.adaptSize,
                                width: 24.adaptSize,
                              ),
                            ),
                          ),
                          suffixConstraints: BoxConstraints(
                            maxHeight: 56.v,
                          ),
                          validator: (value) {
                            if (value == null ||
                                (!isValidPassword(value, isRequired: true))) {
                              return "err_msg_please_enter_valid_password".tr;
                            }
                            return null;
                          },
                          obscureText: !welcomeBackState.isShowPassword,
                        ),
                      ),
                      SizedBox(height: 8.v),
                      Align(
                        alignment: Alignment.centerRight,
                        child: GestureDetector(
                          onTap: () {
                            onTapTxtForgotPassword(context);
                          },
                          child: Padding(
                            padding: EdgeInsets.only(right: 32.h),
                            child: Text(
                              "msg_forgot_password".tr,
                              style: CustomTextStyles.titleSmallOrange300,
                            ),
                          ),
                        ),
                      ),
                      SizedBox(height: 24.v),
                      
                      // MODIFIED: Continue button with bathroom API integration
                      Consumer(
                        builder: (context, ref, child) {
                          return BaseButton(
                            text: _isSyncingBathroomApi 
                                ? "Syncing..." 
                                : "lbl_continue".tr,
                            buttonTextStyle: theme.textTheme.titleLarge,
                            margin: EdgeInsets.only(
                              left: 12.h,
                              right: 12.h,
                            ),
                            buttonStyle: CustomButtonStyles.none,
                            decoration: CustomButtonStyles
                                .gradientPrimaryToPrimaryContainerDecoration,
                            decorationPressed: CustomButtonStyles
                                .gradientPrimaryToPrimaryContainerDecorationPressed,
                            onPressed: _isSyncingBathroomApi 
                                ? null 
                                : () => _handleLogin(welcomeBackState),
                          );
                        },
                      ),
                      
                      // ADD THIS: Show bathroom API sync status
                      if (_isSyncingBathroomApi)
                        Padding(
                          padding: EdgeInsets.only(top: 12.v),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                    theme.colorScheme.primary,
                                  ),
                                ),
                              ),
                              SizedBox(width: 8.h),
                              Text(
                                "Connecting to layout service...",
                                style: theme.textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),

                      Spacer(),
                      CustomImageView(
                        imagePath: ImageConstant.imgGoldLongLogo,
                        height: 64.v,
                      ),
                      SizedBox(height: 24.v),
                      GestureDetector(
                        onTap: () {
                          onTapTxtDonthaveaccount(context);
                        },
                        child: RichText(
                          text: TextSpan(
                            children: [
                              TextSpan(
                                text: "msg_don_t_have_account2".tr,
                                style: CustomTextStyles.titleSmallfff5f2f0,
                              ),
                              const TextSpan(
                                text: " ",
                              ),
                              TextSpan(
                                text: "lbl_sign_up".tr,
                                style: CustomTextStyles.titleSmallffd1ac65,
                              )
                            ],
                          ),
                          textAlign: TextAlign.left,
                        ),
                      ),
                      SizedBox(height: 38.v)
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // MODIFIED: Enhanced login handler with bathroom API integration
  Future<void> _handleLogin(dynamic welcomeBackState) async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final email = welcomeBackState.emailController.text;
    final password = welcomeBackState.passwordController.text;

    try {
      // Step 1: AWS Cognito login
      print('🔐 Step 1: Logging in with AWS Cognito...');
      await _awsAuth.signInUser(
        email: email,
        password: password,
      );
      
      print('✅ AWS Cognito login successful');

      // Step 2: Sync with Bathroom API (non-blocking)
      setState(() => _isSyncingBathroomApi = true);
      
      print('🔐 Step 2: Syncing with Bathroom API...');
      final bathroomApiSuccess = await _bathroomApi.syncWithAwsLogin(
        email: email,
        password: password,
      );

      setState(() => _isSyncingBathroomApi = false);

      if (bathroomApiSuccess) {
        print('✅ Bathroom API sync successful');
        // Show success message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Bathroom layout service connected'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 2),
            ),
          );
        }
      } else {
        print('⚠️ Bathroom API sync failed (non-critical)');
        // Show warning but don't block navigation
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('⚠️ Layout service unavailable (you can still use the app)'),
              backgroundColor: Colors.orange,
              duration: Duration(seconds: 3),
            ),
          );
        }
      }

      // Step 3: Navigate to home screen
      // Note: Navigation happens regardless of bathroom API status
      if (mounted) {
        // Uncomment when ready:
        // NavigatorService.pushNamed(
        //   AppRoutes.homeScreen,
        //   arguments: email,
        // );
      }

    } catch (e) {
      setState(() => _isSyncingBathroomApi = false);
      print('❌ Login error: $e');
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Login failed: ${e.toString()}'),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    }
  }

  /// Navigates to the forgotPasswordScreen when the action is triggered.
  onTapTxtForgotPassword(BuildContext context) {
    NavigatorService.pushNamed(
      AppRoutes.forgotPasswordScreen,
    );
  }

  /// Navigates to the createAccountScreen when the action is triggered.
  onTapTxtDonthaveaccount(BuildContext context) {
    NavigatorService.pushNamed(
      AppRoutes.createAccountScreen,
    );
  }
}

/// Example: How to use bathroom layouts in your app
/// 
/// After login, you can generate layouts like this:
/// 
/// ```dart
/// final bathroomApi = BathroomApiAuthService();
/// 
/// // Generate a layout
/// final layout = await bathroomApi.generateLayout(
///   roomWidth: 300,
///   roomDepth: 240,
///   roomHeight: 280,
///   objectsToPlace: ['toilet', 'sink', 'shower'],
/// );
/// 
/// if (layout != null) {
///   print('Layout ID: ${layout['layout_id']}');
///   print('Score: ${layout['score']}');
///   print('Objects: ${layout['objects']}');
/// }
/// 
/// // Get all user's layouts
/// final layouts = await bathroomApi.getUserLayouts();
/// 
/// // Delete a layout
/// await bathroomApi.deleteLayout('layout_id');
/// ```
