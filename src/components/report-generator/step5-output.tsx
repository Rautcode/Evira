
"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { FileText, FileSpreadsheet, Mail, FolderOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "../ui/textarea";

const outputOptionsSchema = z.object({
  format: z.enum(["pdf", "csv"], {
    required_error: "You need to select an output format.",
  }),
  fileName: z.string().min(1, "File name is required.").default(`report_${new Date().toISOString().split('T')[0]}`),
  location: z.string().optional(), // This would typically involve a folder picker, simplified for now
  emailImmediately: z.boolean().default(false),
  recipients: z.string().optional().refine(val => {
    if (!val || val.trim() === "") return true; // Optional if not emailing
    return val.split(',').every(email => z.string().email().safeParse(email.trim()).success);
  }, "Please provide valid email addresses, separated by commas."),
  emailMessage: z.string().optional(),
});

import { useFormContext } from "react-hook-form";

export function ReportStep5Output() {
  const form = useFormContext();
  const emailImmediately = form?.watch("emailImmediately") || false;

  return (
    <Form {...form}>
      <div className="space-y-8 p-4">
        <FormField
          control={form.control}
          name="format"
          render={({ field }) => (
            <FormItem className="space-y-3">
              <FormLabel>Output Format</FormLabel>
              <FormControl>
                <RadioGroup
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                  className="flex flex-col sm:flex-row gap-4"
                >
                  <FormItem className="flex items-center space-x-3 space-y-0 p-4 border rounded-md flex-1 hover:bg-muted has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5">
                    <FormControl>
                      <RadioGroupItem value="pdf" />
                    </FormControl>
                    <FormLabel className="font-normal cursor-pointer flex items-center w-full">
                      <FileText className="mr-2 h-5 w-5 text-red-600" /> PDF Document
                    </FormLabel>
                  </FormItem>
                  <FormItem className="flex items-center space-x-3 space-y-0 p-4 border rounded-md flex-1 hover:bg-muted has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5">
                    <FormControl>
                      <RadioGroupItem value="csv" />
                    </FormControl>
                    <FormLabel className="font-normal cursor-pointer flex items-center w-full">
                      <FileSpreadsheet className="mr-2 h-5 w-5 text-green-600" /> CSV File
                    </FormLabel>
                  </FormItem>
                </RadioGroup>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="fileName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Output File Name</FormLabel>
              <FormControl>
                <Input placeholder="e.g., Daily_Production_Report" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormItem>
          <FormLabel>Location</FormLabel>
          <div className="flex gap-2 items-center">
            <FormControl>
              <Input placeholder="e.g., C:\\Reports\\SCADA" disabled value={form.getValues("location") || "Default Location"} />
            </FormControl>
            <Button type="button" variant="outline" disabled> {/* Folder picker is complex for web */}
              <FolderOpen className="mr-2 h-4 w-4" /> Browse
            </Button>
          </div>
          <FormDescription>
            Select a location to save the report. (Feature currently illustrative)
          </FormDescription>
        </FormItem>

        <FormField
          control={form.control}
          name="emailImmediately"
          render={({ field }) => (
             <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                    <FormLabel className="text-base flex items-center">
                        <Mail className="mr-2 h-5 w-5 text-primary" /> Email Report Immediately
                    </FormLabel>
                    <FormDescription>
                        Send the generated report via email upon completion.
                    </FormDescription>
                </div>
                <FormControl>
                <Switch
                    checked={field.value}
                    onCheckedChange={field.onChange}
                />
                </FormControl>
            </FormItem>
          )}
        />

        {emailImmediately && (
          <>
            <FormField
              control={form.control}
              name="recipients"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Recipients</FormLabel>
                  <FormControl>
                    <Input placeholder="john.doe@example.com, jane.doe@example.com" {...field} />
                  </FormControl>
                  <FormDescription>
                    Comma-separated email addresses.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
             <FormField
              control={form.control}
              name="emailMessage"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email Message (Optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter a custom message for the email body..."
                      className="resize-none"
                      {...field}
                      rows={3}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        )}
      </div>
    </Form>
  );
}
