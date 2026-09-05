import React, { useRef, useState } from 'react';
import { apiClient } from '../data/apiClient';
import { DashboardPayload } from '../types/meeting';
import {
  AlertCircle,
  CheckCircle2,
  FileAudio,
  FileText,
  Loader2,
  Play,
  Type,
  UploadCloud,
  X,
} from 'lucide-react';

type InputMode = 'AUDIO' | 'TRANSCRIPT_FILE' | 'TRANSCRIPT_TEXT';

interface MeetingInputWidgetProps {
  onProcessingSuccess: (payload: DashboardPayload) => void;
  onProcessingStart?: () => void;
  onProcessingError?: (err: string) => void;
}

export const MeetingInputWidget: React.FC<MeetingInputWidgetProps> = ({
  onProcessingSuccess,
  onProcessingStart,
  onProcessingError,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [meetingId, setMeetingId] = useState('');
  const [mode, setMode] = useState<InputMode>('TRANSCRIPT_FILE');

  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  const [transcriptText, setTranscriptText] = useState('');

  const [status, setStatus] = useState<'IDLE' | 'UPLOADING' | 'PROCESSING' | 'SUCCESS' | 'ERROR'>(
    'IDLE'
  );
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (mode === 'AUDIO') {
        setAudioFile(file);
      } else if (mode === 'TRANSCRIPT_FILE') {
        setTranscriptFile(file);
      }
      setErrorMessage(null);
    }
  };

  const handleModeChange = (newMode: InputMode) => {
    setMode(newMode);
    setAudioFile(null);
    setTranscriptFile(null);
    setTranscriptText('');
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!meetingId.trim()) {
      setErrorMessage('Please specify a valid Meeting ID.');
      return;
    }

    if (mode === 'AUDIO' && !audioFile) {
      setErrorMessage('Please select an audio file (.wav, .mp3, .m4a, etc.).');
      return;
    }

    if (mode === 'TRANSCRIPT_FILE' && !transcriptFile) {
      setErrorMessage('Please select a transcript file (.txt or .json).');
      return;
    }

    if (mode === 'TRANSCRIPT_TEXT' && !transcriptText.trim()) {
      setErrorMessage('Please enter or paste transcript text.');
      return;
    }

    try {
      setStatus('UPLOADING');
      setStatusMessage('Uploading meeting data to Backend API (http://localhost:8000)...');
      if (onProcessingStart) {
        onProcessingStart();
      }

      const payload = await apiClient.processMeeting({
        meetingId: meetingId.trim(),
        audioFile: mode === 'AUDIO' ? audioFile : null,
        transcriptFile: mode === 'TRANSCRIPT_FILE' ? transcriptFile : null,
        transcriptText: mode === 'TRANSCRIPT_TEXT' ? transcriptText : undefined,
      });

      setStatus('SUCCESS');
      setStatusMessage(
        `Successfully processed meeting ${payload.meeting_id} with ${payload.total_canonical_items} action items!`
      );
      onProcessingSuccess(payload);
    } catch (err: any) {
      setStatus('ERROR');
      const errText = err.message || 'Processing failed.';
      setErrorMessage(errText);
      if (onProcessingError) {
        onProcessingError(errText);
      }
    }
  };

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
        marginBottom: '24px',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isOpen ? '16px' : '0',
          cursor: 'pointer',
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <UploadCloud size={20} color="var(--primary)" />
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
            Process Meeting Input (Real Backend Pipeline)
          </h2>
          <span className="meeting-pill">FastAPI Integration</span>
        </div>
        <button
          type="button"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '0.82rem',
          }}
        >
          {isOpen ? 'Collapse [-]' : 'Expand [+]'}
        </button>
      </div>

      {isOpen && (
        <form onSubmit={handleSubmit}>
          {/* Input Mode Selector & Meeting ID */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 16,
              alignItems: 'center',
              marginBottom: 16,
            }}
          >
            {/* Meeting ID */}
            <div style={{ flex: '1 1 200px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)',
                  marginBottom: 6,
                  fontWeight: 600,
                }}
              >
                Meeting ID:
              </label>
              <input
                type="text"
                className="search-input"
                style={{ padding: '8px 12px' }}
                value={meetingId}
                onChange={(e) => setMeetingId(e.target.value)}
                placeholder="e.g. ES2002a or TEST_01"
                disabled={status === 'UPLOADING' || status === 'PROCESSING'}
              />
            </div>

            {/* Mode Buttons */}
            <div style={{ flex: '2 1 320px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)',
                  marginBottom: 6,
                  fontWeight: 600,
                }}
              >
                Input Source:
              </label>
              <div className="role-switcher" style={{ width: 'fit-content' }}>
                <button
                  type="button"
                  className={`role-btn ${mode === 'AUDIO' ? 'active' : ''}`}
                  onClick={() => handleModeChange('AUDIO')}
                >
                  <FileAudio size={14} /> Upload Audio
                </button>
                <button
                  type="button"
                  className={`role-btn ${mode === 'TRANSCRIPT_FILE' ? 'active' : ''}`}
                  onClick={() => handleModeChange('TRANSCRIPT_FILE')}
                >
                  <FileText size={14} /> Upload Transcript
                </button>
                <button
                  type="button"
                  className={`role-btn ${mode === 'TRANSCRIPT_TEXT' ? 'active' : ''}`}
                  onClick={() => handleModeChange('TRANSCRIPT_TEXT')}
                >
                  <Type size={14} /> Paste Transcript
                </button>
              </div>
            </div>
          </div>

          {/* Input Mode Specific Control */}
          <div
            style={{
              background: 'var(--bg-card-subtle)',
              border: '1px dashed var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              marginBottom: 16,
            }}
          >
            {mode === 'AUDIO' && (
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".wav,.mp3,.m4a,.flac,.ogg,.webm,.mp4"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="audio-file-input"
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <button
                    type="button"
                    className="role-btn active"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Select Audio File
                  </button>
                  <span style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                    {audioFile ? audioFile.name : 'No audio file selected (.wav, .mp3, .m4a supported)'}
                  </span>
                  {audioFile && (
                    <button
                      type="button"
                      onClick={() => setAudioFile(null)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              </div>
            )}

            {mode === 'TRANSCRIPT_FILE' && (
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".txt,.json"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="transcript-file-input"
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <button
                    type="button"
                    className="role-btn active"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Select Transcript File
                  </button>
                  <span style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                    {transcriptFile
                      ? transcriptFile.name
                      : 'No transcript selected (supports .txt or .json transcript files)'}
                  </span>
                  {transcriptFile && (
                    <button
                      type="button"
                      onClick={() => setTranscriptFile(null)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                      }}
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              </div>
            )}

            {mode === 'TRANSCRIPT_TEXT' && (
              <div>
                <textarea
                  className="search-input"
                  style={{
                    width: '100%',
                    height: '110px',
                    padding: '10px 12px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    resize: 'vertical',
                  }}
                  placeholder="Paste dialogue transcript here, e.g.:&#10;SPEAKER_00: Let's discuss the remote control design.&#10;SPEAKER_03: The next meeting is in 30 minutes."
                  value={transcriptText}
                  onChange={(e) => {
                    setTranscriptText(e.target.value);
                    setErrorMessage(null);
                  }}
                />
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    marginTop: 4,
                    textAlign: 'right',
                  }}
                >
                  {transcriptText.length} characters
                </div>
              </div>
            )}
          </div>

          {/* Action Button & Status Feedback */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            <button
              type="submit"
              className="role-btn active"
              disabled={status === 'UPLOADING' || status === 'PROCESSING'}
              style={{ padding: '10px 22px', fontSize: '0.9rem' }}
            >
              {status === 'UPLOADING' || status === 'PROCESSING' ? (
                <>
                  <Loader2 size={16} className="spinner" style={{ animation: 'spin 1s linear infinite' }} />
                  Processing Pipeline...
                </>
              ) : (
                <>
                  <Play size={16} /> Process Meeting
                </>
              )}
            </button>

            {/* Error Message */}
            {errorMessage && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  color: 'var(--priority-high)',
                  fontSize: '0.85rem',
                }}
              >
                <AlertCircle size={16} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success / Status Message */}
            {status === 'SUCCESS' && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  color: 'var(--conf-high)',
                  fontSize: '0.85rem',
                }}
              >
                <CheckCircle2 size={16} />
                <span>{statusMessage}</span>
              </div>
            )}
          </div>
        </form>
      )}
    </div>
  );
};
