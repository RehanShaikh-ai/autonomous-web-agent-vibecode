import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PipelineStages } from './components/PipelineStages';
import { TaskInput } from './components/TaskInput';
import { GoalCard } from './components/GoalCard';
import { PlanStepList } from './components/PlanStepList';
import { LiveBrowserView } from './components/LiveBrowserView';
import { VerificationDashboard } from './components/VerificationDashboard';
import { ScreenshotModal, RawDomModal } from './components/Modals';
import { AgentApiClient } from './services/api';
import {
  GoalSchema,
  FinalReport,
  HealthResponse,
  PipelineStage,
  StepRecord,
} from './types/schemas';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [goal, setGoal] = useState<GoalSchema | null>(null);
  const [steps, setSteps] = useState<StepRecord[]>([]);
  const [activeStepId, setActiveStepId] = useState<number | null>(null);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [currentStage, setCurrentStage] = useState<PipelineStage | 0>(0);
  const [isExecuting, setIsExecuting] = useState(false);

  // Modals
  const [screenshotModalPath, setScreenshotModalPath] = useState<string | null>(null);
  const [rawDomModal, setRawDomModal] = useState<{ html: string; stepId: number } | null>(null);

  useEffect(() => {
    AgentApiClient.checkHealth().then(setHealth);
  }, []);

  const handleReset = () => {
    setGoal(null);
    setSteps([]);
    setActiveStepId(null);
    setFinalReport(null);
    setCurrentStage(0);
    setIsExecuting(false);
  };

  const handleExecute = async (query: string, maxSteps: number) => {
    handleReset();
    setIsExecuting(true);

    try {
      // Stage 1 & 2: Understand & Plan
      setCurrentStage(1);
      const planRes = await AgentApiClient.generatePlan(query, maxSteps);
      setGoal(planRes.structured_goal);

      setCurrentStage(2);
      const initialStepRecords: StepRecord[] = planRes.steps.map((s) => ({
        step: s,
        status: 'pending',
      }));
      setSteps(initialStepRecords);
      setActiveStepId(initialStepRecords[0]?.step.step_id || 1);

      // Stage 3: Browse & Process
      setCurrentStage(3);
      const extractedEntitiesList: Array<Record<string, any>> = [];

      for (let i = 0; i < initialStepRecords.length; i++) {
        const current = initialStepRecords[i];
        setActiveStepId(current.step.step_id);

        // Update status to running
        setSteps((prev) =>
          prev.map((s, idx) => (idx === i ? { ...s, status: 'running' } : s))
        );

        const startTime = Date.now();
        const browseRes = await AgentApiClient.executeBrowse(
          planRes.goal_id,
          current.step
        );

        const processRes = await AgentApiClient.processPage(
          planRes.goal_id,
          current.step.step_id,
          browseRes.raw_html
        );

        if (processRes.entities && Object.keys(processRes.entities).length > 0) {
          extractedEntitiesList.push(processRes.entities);
        }

        const durationMs = Date.now() - startTime;

        setSteps((prev) =>
          prev.map((s, idx) =>
            idx === i
              ? {
                  ...s,
                  browserResult: browseRes,
                  processedPage: processRes,
                  status: browseRes.status,
                  durationMs,
                }
              : s
          )
        );
      }

      // Stage 4: Verify
      setCurrentStage(4);
      const reportRes = await AgentApiClient.verifyData(
        planRes.goal_id,
        extractedEntitiesList
      );

      // Stage 5: Deliver
      setCurrentStage(5);
      setFinalReport(reportRes);
    } catch (err) {
      console.error('Execution failure in agent pipeline:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const activeRecord = steps.find((s) => s.step.step_id === activeStepId) || steps[0] || null;

  return (
    <div className="app-container">
      {/* Header */}
      <Header health={health} onReset={handleReset} isExecuting={isExecuting} />

      {/* 5-Stage Stepper Tracker */}
      <PipelineStages currentStage={currentStage} isCompleted={currentStage === 5 && !isExecuting} />

      {/* Task Input Prompt Bar */}
      <TaskInput onExecute={handleExecute} isExecuting={isExecuting} />

      {/* Main Multi-Stage Work Area */}
      {(goal || steps.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem', alignItems: 'start' }}>
          {/* Left Column: Goal & Plan Steps */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {goal && <GoalCard goal={goal} />}
            {steps.length > 0 && (
              <PlanStepList
                steps={steps}
                activeStepId={activeStepId}
                onSelectStep={setActiveStepId}
              />
            )}
          </div>

          {/* Right Column: Live Viewport & Telemetry */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <LiveBrowserView
              activeRecord={activeRecord}
              onOpenScreenshot={setScreenshotModalPath}
              onOpenRawDom={(html, stepId) => setRawDomModal({ html, stepId })}
            />
          </div>
        </div>
      )}

      {/* Stage 5 Verified Report Delivery */}
      {finalReport && (
        <VerificationDashboard
          report={finalReport}
          onOpenScreenshot={setScreenshotModalPath}
        />
      )}

      {/* Modals */}
      <ScreenshotModal
        isOpen={Boolean(screenshotModalPath)}
        screenshotPath={screenshotModalPath}
        onClose={() => setScreenshotModalPath(null)}
      />

      <RawDomModal
        isOpen={Boolean(rawDomModal)}
        rawHtml={rawDomModal?.html || null}
        stepId={rawDomModal?.stepId || null}
        onClose={() => setRawDomModal(null)}
      />
    </div>
  );
};
