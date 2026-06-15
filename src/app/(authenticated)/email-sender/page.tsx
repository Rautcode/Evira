"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Mail } from 'lucide-react';
import { sendEmail } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

export default function EmailSenderPage() {
  const [to, setTo] = React.useState('');
  const [subject, setSubject] = React.useState('');
  const [body, setBody] = React.useState('');
  const [sending, setSending] = React.useState(false);
  const [success, setSuccess] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setSuccess(null);
    setError(null);
    try {
      await sendEmail({ to, subject, body });
      setSuccess('Email sent successfully!');
      setTo('');
      setSubject('');
      setBody('');
    } catch (err) {
      setError('Failed to send email.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center text-2xl font-bold">
            <Mail className="mr-3 h-7 w-7 text-primary" />
            Email Sender
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSend} className="space-y-4 max-w-lg mx-auto">
            <Input
              placeholder="Recipient Email(s)"
              value={to}
              onChange={e => setTo(e.target.value)}
              required
              type="email"
              multiple
            />
            <Input
              placeholder="Subject"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              required
            />
            <Textarea
              placeholder="Email body..."
              value={body}
              onChange={e => setBody(e.target.value)}
              rows={5}
              required
            />
            <Button type="submit" className="w-full" disabled={sending}>
              {sending ? 'Sending...' : 'Send Email'}
            </Button>
            {success && <div className="text-green-600 text-center mt-2">{success}</div>}
            {error && <div className="text-destructive text-center mt-2">{error}</div>}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
