import React, { useEffect, useState } from 'react';
import { interviewsApi } from '../../api/interviews';
import { jobsApi } from '../../api/jobs';
import { getErrorMessage } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorBanner from '../../components/ErrorBanner';
import EmptyState from '../../components/EmptyState';
import StatusBadge from '../../components/StatusBadge';

export default function InterviewPractice() {
  const [sessions, setSessions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadSessions = () => {
    interviewsApi
      .mySessions()
      .then(setSessions)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(loadSessions, []);

  if (selectedId) {
    return (
      <SessionDetail
        sessionId={selectedId}
        onBack={() => {
          setSelectedId(null);
          loadSessions();
        }}
      />
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Interview Practice</h1>
      <NewSessionForm onCreated={(session) => setSelectedId(session.id)} />

      <h2 className="mt-8 mb-3 text-lg font-semibold text-gray-900">Your sessions</h2>
      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : sessions.length === 0 ? (
        <EmptyState title="No interview sessions yet" message="Start one above to begin practicing." />
      ) : (
        <div className="flex flex-col gap-3">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedId(s.id)}
              className="card flex items-center justify-between text-left hover:shadow-md"
            >
              <div>
                <p className="font-medium text-gray-900 capitalize">
                  {s.interview_type} &middot; {s.difficulty} &middot; {s.experience_level}
                </p>
                {s.job_id && <p className="text-xs text-gray-500">Linked to job #{s.job_id}</p>}
              </div>
              <div className="flex items-center gap-3">
                {s.overall_score != null && (
                  <span className="text-sm font-semibold text-brand-700">{s.overall_score}/10</span>
                )}
                <StatusBadge status={s.status} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function NewSessionForm({ onCreated }) {
  const { showToast } = useToast();
  const [jobs, setJobs] = useState([]);
  const [form, setForm] = useState({
    interview_type: 'technical',
    difficulty: 'medium',
    experience_level: 'fresher',
    job_id: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    jobsApi
      .list({ status: 'open', page: 1, page_size: 50 })
      .then((data) => setJobs(data.items))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const session = await interviewsApi.createSession({
        ...form,
        job_id: form.job_id ? Number(form.job_id) : null,
      });
      showToast('Interview session started', 'success');
      onCreated(session);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="card mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
      <div>
        <label className="text-sm font-medium text-gray-700">Type</label>
        <select className="input" value={form.interview_type} onChange={(e) => setForm({ ...form, interview_type: e.target.value })}>
          <option value="technical">Technical</option>
          <option value="hr">HR</option>
          <option value="behavioral">Behavioral</option>
        </select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-700">Difficulty</label>
        <select className="input" value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-700">Experience</label>
        <select
          className="input"
          value={form.experience_level}
          onChange={(e) => setForm({ ...form, experience_level: e.target.value })}
        >
          <option value="fresher">Fresher</option>
          <option value="experienced">Experienced</option>
        </select>
      </div>
      <div>
        <label className="text-sm font-medium text-gray-700">Job (optional)</label>
        <select className="input" value={form.job_id} onChange={(e) => setForm({ ...form, job_id: e.target.value })}>
          <option value="">Generic practice</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>
              {j.title}
            </option>
          ))}
        </select>
      </div>
      <div className="col-span-2 md:col-span-4">
        <ErrorBanner message={error} />
        <button type="submit" disabled={submitting} className="btn-primary mt-2">
          {submitting ? 'Starting…' : 'Start interview'}
        </button>
      </div>
    </form>
  );
}

function SessionDetail({ sessionId, onBack }) {
  const [session, setSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const load = () => {
    Promise.all([interviewsApi.getSession(sessionId), interviewsApi.getQuestions(sessionId)])
      .then(([s, q]) => {
        setSession(s);
        setQuestions(q);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(load, [sessionId]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      await interviewsApi.generateQuestions(sessionId, 5);
      load();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <button onClick={onBack} className="text-sm text-brand-600 hover:underline">
        &larr; Back to sessions
      </button>

      <div className="mt-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold capitalize text-gray-900">
          {session.interview_type} interview &middot; {session.difficulty}
        </h1>
        <div className="flex items-center gap-3">
          {session.overall_score != null && (
            <span className="text-lg font-semibold text-brand-700">{session.overall_score}/10</span>
          )}
          <StatusBadge status={session.status} />
        </div>
      </div>

      <ErrorBanner message={error} />

      <button onClick={handleGenerate} disabled={generating} className="btn-primary mt-4">
        {generating ? 'Generating…' : questions.length === 0 ? 'Generate questions' : 'Generate more questions'}
      </button>

      <div className="mt-6 flex flex-col gap-4">
        {questions.length === 0 ? (
          <EmptyState title="No questions yet" message="Click 'Generate questions' to start." />
        ) : (
          questions.map((q) => <QuestionCard key={q.id} question={q} onChange={load} />)
        )}
      </div>
    </div>
  );
}

function QuestionCard({ question, onChange }) {
  const [answer, setAnswer] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    interviewsApi
      .getAnswer(question.id)
      .then(setAnswer)
      .catch(() => setAnswer(null))
      .finally(() => setLoading(false));
  }, [question.id]);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      const created = await interviewsApi.submitAnswer(question.id, answerText);
      setAnswer(created);
      onChange?.();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleEvaluate = async () => {
    setEvaluating(true);
    setError('');
    try {
      const evaluated = await interviewsApi.evaluateAnswer(question.id);
      setAnswer(evaluated);
      onChange?.();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="card">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{question.category}</p>
      <p className="mt-1 font-medium text-gray-900">{question.question_text}</p>

      <ErrorBanner message={error} />

      {!answer ? (
        <div className="mt-3">
          <textarea
            className="input"
            rows={3}
            placeholder="Type your answer…"
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
          />
          <button onClick={handleSubmit} disabled={submitting || !answerText.trim()} className="btn-primary mt-2">
            {submitting ? 'Submitting…' : 'Submit answer'}
          </button>
        </div>
      ) : (
        <div className="mt-3">
          <p className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">{answer.answer_text}</p>

          {answer.score == null ? (
            <button onClick={handleEvaluate} disabled={evaluating} className="btn-primary mt-2">
              {evaluating ? 'Evaluating…' : 'Get AI feedback'}
            </button>
          ) : (
            <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50 p-3">
              <p className="text-sm font-semibold text-brand-700">Score: {answer.score}/10</p>
              <p className="mt-1 text-sm text-gray-700">{answer.feedback_summary}</p>
              {answer.good_points_json?.length > 0 && (
                <p className="mt-2 text-xs text-gray-600">
                  <span className="font-semibold">Good:</span> {answer.good_points_json.join('; ')}
                </p>
              )}
              {answer.improvements_json?.length > 0 && (
                <p className="mt-1 text-xs text-gray-600">
                  <span className="font-semibold">Improve:</span> {answer.improvements_json.join('; ')}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
