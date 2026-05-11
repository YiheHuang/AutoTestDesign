@echo off
echo ========================================
echo   AutoTestDesign - 端到端测试运行脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 清理数据库...
del /q flask_app\data.db 2>nul

echo [2/3] 生成测试用例...
python -c "from src.parser.code_parser import CodeParser; from src.models.requirement import *; from src.risk.risk_analyzer import RiskAnalyzer; from src.test_design.black_box.orchestrator import BlackBoxOrchestrator; from src.test_design.white_box.whitebox_orchestrator import WhiteBoxOrchestrator; from src.test_design.oracle.oracle_generator import OracleGenerator; from src.models.testcase import TestSuite; from src.export.pytest_exporter import export_pytest_quick; parser = CodeParser(); cs = parser.parse_file('flask_app/app.py'); req = StructuredRequirement(id='REQ-001', source=SourceType.TEXT, raw_text='', title='注册登录系统', description='', input_fields=[InputField(name='username',data_type='string',valid_range='3-20',constraints=['required','min_length:3','max_length:20','alphanumeric','unique']),InputField(name='password',data_type='string',valid_range='8-32',constraints=['required']),InputField(name='confirm_password',data_type='string',constraints=['required']),InputField(name='email',data_type='string',constraints=['required','format:email','unique']),InputField(name='age',data_type='integer',valid_range='18-120',constraints=['required','min:18','max:120'])], conditions=[Condition(description='用户名已存在'),Condition(description='年龄<18')], expected_behaviors=[SystemBehavior(condition='有效',action='创建',expected_output='注册成功'),SystemBehavior(condition='用户名重复',action='拒绝',expected_output='用户名已被注册'),SystemBehavior(condition='未成年',action='拒绝',expected_output='未成年不可注册')], domain='web_application'); risk = RiskAnalyzer()._heuristic_analyze(req); bb = BlackBoxOrchestrator().generate_all(req,['EP','BVA'],use_ai=False); wb = WhiteBoxOrchestrator().generate_all(req,cs,enabled_techniques=['LogicCoverage','PathCoverage']); all_cases=bb.test_cases+wb.test_cases; combined=TestSuite(id='TS-ALL',name='完整套件',requirement_id=req.id,test_cases=all_cases); oracle=OracleGenerator(); validated=oracle.generate_suite(combined,req,cs,validate=True); code=export_pytest_quick([validated],'flask_app/tests/test_generated.py'); print(f'生成完成: {len(validated.test_cases)} 个测试用例');"

echo [3/3] 运行测试...
python -m pytest flask_app/tests/test_generated.py -v --tb=short

echo.
echo ========================================
echo   测试完成！
echo ========================================
pause
